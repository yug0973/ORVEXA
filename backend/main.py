import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.routers import satellites, conjunctions, reentry, solar, ws_swarm, compliance, copilot

# ─────────────────────────────────────────────
# API Key Authentication Middleware
# Protects mutating routes (POST/PATCH/DELETE)
# ─────────────────────────────────────────────
# Set ORVEXA_API_KEY in your .env for production.
# Default dev key allows local testing without extra config.
_DEFAULT_DEV_API_KEY = "ORVEXA-dev-2026"

class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Require X-API-Key header on all write (non-GET/non-WS) requests."""
    PROTECTED_PREFIXES = ("/api/compliance", "/api/satellites/import")
    OPEN_METHODS = {"GET", "OPTIONS", "HEAD"}

    def __init__(self, app, api_key: str):
        super().__init__(app)
        self.api_key = api_key

    async def dispatch(self, request: Request, call_next):
        # Skip open methods, docs, health, root, and websockets
        if request.method in self.OPEN_METHODS:
            return await call_next(request)
        if request.url.path.startswith(("/docs", "/openapi", "/redoc", "/health", "/", "/api/ws", "/models")):
            return await call_next(request)
        # Protect only designated write routes
        if any(request.url.path.startswith(p) for p in self.PROTECTED_PREFIXES):
            key = request.headers.get("X-API-Key", "")
            if key != self.api_key:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or missing API key. Include 'X-API-Key' header."},
                    headers={"WWW-Authenticate": "ApiKey"}
                )
        return await call_next(request)

# Lightweight in-memory sliding window rate limiter (120 requests/minute per client IP)
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_records = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Exclude static files, docs, openapi, and websockets from strict rate limiting
        path = request.url.path
        if path.startswith("/models") or path.startswith("/docs") or path.startswith("/openapi.json") or path.startswith("/api/ws"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Clean timestamps older than window
        timestamps = [t for t in self.request_records[client_ip] if now - t < self.window_seconds]
        
        if len(timestamps) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded (120 req/min). Please try again shortly."},
                headers={
                    "Retry-After": str(int(self.window_seconds - (now - timestamps[0]))),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        timestamps.append(now)
        self.request_records[client_ip] = timestamps
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.max_requests - len(timestamps)))
        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    On startup, verify if the database contains any satellites.
    If empty or uninitialized, run the database seeders to populate initial demo data.
    """
    from backend.db.models import Satellite, StateVector, ConjunctionEvent, ReentryAlert, ComplianceFiling
    from sqlalchemy import select, func
    from datetime import datetime, timezone
    from backend.seed_db import seed as seed_db
    from backend.seed_reentry import seed as seed_reentry
    from backend.db.connection import AsyncSessionLocal
    
    run_seeding = False
    async with AsyncSessionLocal() as session:
        try:
            # 1. Check if we have any satellites
            result = await session.execute(select(Satellite).limit(1))
            sat = result.scalars().first()
            if not sat:
                run_seeding = True
            else:
                # 2. Check if the state vectors are outdated
                max_epoch_res = await session.execute(select(func.max(StateVector.epoch)))
                max_epoch = max_epoch_res.scalar()
                
                if max_epoch:
                    # Make it timezone-aware if naive
                    if max_epoch.tzinfo is None:
                        max_epoch = max_epoch.replace(tzinfo=timezone.utc)
                    
                    now_utc = datetime.now(timezone.utc)
                    
                    if max_epoch < now_utc:
                        print(f"ORVEXA: DB contains outdated state vectors (latest: {max_epoch}, now: {now_utc}). Clearing and re-seeding...")
                        
                        # Clear old records to allow fresh generation starting today
                        await session.execute(StateVector.__table__.delete())
                        await session.execute(ConjunctionEvent.__table__.delete())
                        await session.execute(ReentryAlert.__table__.delete())
                        await session.execute(ComplianceFiling.__table__.delete())
                        await session.execute(Satellite.__table__.delete())
                        await session.commit()
                        
                        run_seeding = True
                    else:
                        print("ORVEXA: DB data detected and up-to-date. Skipping automatic seed.")
                else:
                    run_seeding = True
        except Exception as e:
            print(f"ORVEXA: Startup check failed or tables not initialized ({e}). Triggering schema generation and seeding...")
            run_seeding = True

    if run_seeding:
        try:
            print("==================================================")
            print("ORVEXA: DB is empty/new. Running automatic seed...")
            print("==================================================")
            await seed_db()
            await seed_reentry()
            print("==================================================")
            print("ORVEXA: Automatic database seeding complete!")
            print("==================================================")
        except Exception as se:
            print(f"ORVEXA: Failed to execute automatic database seeding: {se}")
    yield

# 1. Instantiate the FastAPI application
app = FastAPI(
    title="ORVEXA Space Safety API",
    description="REST API serving Space Situational Awareness, conjunction hazards, reentry alerts, and solar weather data.",
    version="1.0.0",
    lifespan=lifespan
)

# 2. Configure CORS middleware with strict domain restrictions for production
origins_env = os.getenv("ALLOWED_ORIGINS", "")
if origins_env:
    origins = [orig.strip() for orig in origins_env.split(",") if orig.strip()]
else:
    # Safe default developer and production Docker origins
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
        "http://127.0.0.1"
    ]

# If in sandbox/development debug mode, allow "*" wildcard
if os.getenv("ENV", "development").lower() == "development":
    origins = ["*"]

_api_key = os.getenv("ORVEXA_API_KEY", _DEFAULT_DEV_API_KEY)
app.add_middleware(ApiKeyMiddleware, api_key=_api_key)
app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Mount Core 4 Pillars + Copilot + NOAA Solar Feeds + Swarm Pipeline
app.include_router(satellites.router)     # Pillar 1: Orbit Globe & SGP4 Catalog
app.include_router(conjunctions.router)   # Pillar 2: Collision Avoidance Hub & B-Plane
app.include_router(reentry.router)        # Pillar 3: Reentry Risk Console & Monte Carlo
app.include_router(solar.router)          # NOAA Space Weather & Aditya-L1 Feeds
app.include_router(compliance.router)     # Pillar 4: Automated Compliance Hub
app.include_router(ws_swarm.router)       # Multi-Stage Automated Pipeline Engine
app.include_router(copilot.router)        # AI Astrometry Copilot Drawer Assistant

# 4. Mount static model assets so Cesium can resolve relative paths
from fastapi.staticfiles import StaticFiles
models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ORVEXA-frontend", "public", "models")
if os.path.exists(models_dir):
    app.mount("/models", StaticFiles(directory=models_dir), name="models")
else:
    # Fallback to local directory relative to current working directory
    app.mount("/models", StaticFiles(directory="ORVEXA-frontend/public/models"), name="models")


@app.get("/")
async def root():
    """
    Root endpoint verifying server status.
    """
    return {
        "status": "online",
        "service": "ORVEXA Space Safety REST API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """
    Standard health check endpoint.
    """
    return {"status": "ok"}

@app.get("/handbook")
@app.get("/api/handbook")
async def get_handbook():
    """
    Directly serves the generated comprehensive Hinglish Handbook PDF.
    """
    from fastapi.responses import FileResponse
    pdf_path = os.path.abspath("ORVEXA_Complete_Project_Handbook_Hinglish.pdf")
    if not os.path.exists(pdf_path):
        pdf_path = os.path.abspath("docs/ORVEXA_Complete_Project_Handbook_Hinglish.pdf")
    if os.path.exists(pdf_path):
        return FileResponse(
            pdf_path, 
            media_type="application/pdf", 
            filename="ORVEXA_Complete_Project_Handbook_Hinglish.pdf"
        )
    return JSONResponse(status_code=404, content={"detail": "Handbook PDF not found."})

if __name__ == "__main__":
    import uvicorn
    # Launch uvicorn programmatically when executed directly
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

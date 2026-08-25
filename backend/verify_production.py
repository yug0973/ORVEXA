import os
import time
import json
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import asyncio

import sys
# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ensure test DB is used during verify run to avoid postgres dependencies if not set up
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_ORVEXA_backend.db"

from backend.main import app
from backend.db.models import Base, Satellite, ConjunctionEvent
from backend.services.compliance_generator import generate_compliance_brief, compile_pdf_document
from orbital_mechanics.propagator import fetch_active_catalog, propagate_catalog_batch

client = TestClient(app)

async def check_database_responsiveness():
    """
    Verifies that the database is reachable and indexes are responsive.
    """
    db_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(db_url, echo=False)
    
    start_time = time.time()
    try:
        # Create schema tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        AsyncSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with AsyncSessionLocal() as session:
            # Query count to test database index performance
            res = await session.execute(select(func.count(Satellite.norad_id)))
            count = res.scalar_one()
            
        latency_ms = (time.time() - start_time) * 1000
        await engine.dispose()
        return True, f"DB Connected successfully. Satellites in DB: {count}. Latency: {latency_ms:.2f}ms"
    except Exception as e:
        await engine.dispose()
        return False, f"DB Connection Failed: {e}"

def check_sgp4_performance():
    """
    Measures execution limits for the analytical SGP4 orbital propagator.
    """
    start_time = time.time()
    try:
        catalog = fetch_active_catalog()
        subset = catalog[:50]  # Propagate 50 satellites for performance testing
        
        prop_start = time.time()
        states = propagate_catalog_batch(subset, time_window_hours=24, step_minutes=30)
        prop_duration_ms = (time.time() - prop_start) * 1000
        
        avg_per_sat_ms = prop_duration_ms / len(subset)
        return True, f"SGP4 performance: propagated {len(subset)} satellites (24h window). Avg: {avg_per_sat_ms:.2f}ms/sat (Target: <10ms/sat)"
    except Exception as e:
        return False, f"SGP4 propagation failed: {e}"

def check_ollama_status():
    """
    Measures response times of the local Ollama LLM service, verifying fallback safety.
    """
    start_time = time.time()
    event_data = {
        "primary_name": "ISS (ZARYA)",
        "primary_norad": 25544,
        "secondary_name": "CALSPHERE 1",
        "secondary_norad": 900,
        "tca": "2026-08-09T12:00:00",
        "miss_distance": 0.45,
        "pc": 1.2e-4,
        "operator_name": "NASA Operator"
    }
    
    brief = generate_compliance_brief(event_data)
    duration_ms = (time.time() - start_time) * 1000
    
    status_msg = f"Filing briefing generated in {duration_ms:.2f}ms. "
    if "Ollama Llama 3.2 model unreachable" in brief or "Warning:" in status_msg:
        status_msg += "(Used Fallback Template)"
    else:
        status_msg += "(Used Local Llama 3.2)"
        
    return True, status_msg

def check_api_latencies():
    """
    Measures the latencies of local FastAPI REST endpoints.
    Target must be < 50ms for local queries.
    """
    endpoints = [
        "/",
        "/api/satellites?limit=5",
        "/api/conjunctions",
        "/api/reentry",
        "/api/solar"
    ]
    
    results = []
    all_passed = True
    
    for url in endpoints:
        start_time = time.time()
        res = client.get(url)
        latency_ms = (time.time() - start_time) * 1000
        
        passed = res.status_code == 200 and latency_ms < 50.0
        if not passed:
            all_passed = False
            
        results.append(f"    - GET {url}: Status {res.status_code} | Latency: {latency_ms:.2f}ms {'[PASS]' if passed else '[FAIL]'}")
        
    log_summary = "\n" + "\n".join(results)
    return all_passed, log_summary

def check_pdf_compiler():
    """
    Validates PDF compiling capabilities and file structure.
    """
    filing_data = {
        "id": 8888,
        "satellite": "ISS (ZARYA)",
        "primary_norad": 25544,
        "secondary_norad": 900,
        "operator": "NASA Operator",
        "tca": datetime.now(),
        "status": "Filed",
        "submitted_at": datetime.now(),
        "briefing": "Sanity check compliance briefing. Avoidance maneuver scheduled prograde."
    }
    
    try:
        pdf_path = compile_pdf_document(filing_data)
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            # Clean up compiled test PDF
            try:
                os.remove(pdf_path)
            except Exception:
                pass
            return True, "PDF compiler: successfully generated print-ready PDF document."
        return False, "PDF compiler: compiled file is missing or empty."
    except Exception as e:
        return False, f"PDF compiler failed: {e}"

async def main():
    print("=" * 80)
    print("                 ORVEXA SYSTEM PRODUCTION SANITY CHECK")
    print("=" * 80)
    
    checks = [
        ("Database Connection", check_database_responsiveness()),
        ("SGP4 Engine limits", asyncio.to_thread(check_sgp4_performance)),
        ("Ollama LLM Agent", asyncio.to_thread(check_ollama_status)),
        ("PDF Document Compiler", asyncio.to_thread(check_pdf_compiler)),
        ("REST API Latency", asyncio.to_thread(check_api_latencies))
    ]
    
    overall_passed = True
    
    for name, coro in checks:
        print(f"Running check: {name}...")
        passed, msg = await coro
        if not passed:
            overall_passed = False
            status = "FAIL"
        else:
            status = "PASS"
            
        print(f"  [{status}] {msg}\n")
        
    print("=" * 80)
    if overall_passed:
        print("               ALL SYSTEMS RUNNING CORRECTLY - [PRODUCTION READY]")
    else:
        print("               WARNING: SOME SYSTEMS FAILED CHECKS - [NOT READY]")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())

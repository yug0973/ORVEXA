import os
import json
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# Set database URL to test SQLite before importing app
TEST_DB_FILE = "test_mvp_features.db"
if os.path.exists(TEST_DB_FILE):
    try:
        os.remove(TEST_DB_FILE)
    except Exception:
        pass

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_FILE}"

from backend.main import app
from backend.db.models import Base, Satellite, StateVector, ConjunctionEvent, ReentryAlert, ComplianceFiling

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    """
    Setup temporary test SQLite database with seed data for MVP testing.
    """
    import asyncio
    test_db_url = f"sqlite+aiosqlite:///{TEST_DB_FILE}"
    engine = create_async_engine(test_db_url, echo=False)
    
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Override get_db dependency in app
    async def override_get_db():
        async with AsyncSessionLocal() as session:
            yield session
            
    from backend.db.connection import get_db
    app.dependency_overrides[get_db] = override_get_db
    
    async def _init():
        # 1. Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            
        # 2. Insert mock seed data
        async with AsyncSessionLocal() as session:
            iss = Satellite(
                norad_id=25544,
                name="ISS (ZARYA)",
                operator="NASA/ROSCOSMOS",
                type="Payload",
                tle1="1 25544U 98067A   20351.52044444  .00001000  00000-0  26000-4 0  9998",
                tle2="2 25544  51.6467  44.5727 0002164  73.9623  34.8726 15.49280000260408",
                updated_at=datetime.now(timezone.utc)
            )
            sec = Satellite(
                norad_id=40001,
                name="DEBRIS MOCK",
                operator="DEBRIS",
                type="Debris",
                tle1="1 40001U 20001A   20351.52044444  .00001000  00000-0  26000-4 0  9998",
                tle2="2 40001  51.6467  44.5727 0002164  73.9623  34.8726 15.49280000260408",
                updated_at=datetime.now(timezone.utc)
            )
            event = ConjunctionEvent(
                id=1,
                primary_norad=25544,
                secondary_norad=40001,
                tca=datetime.now(timezone.utc) + timedelta(days=1),
                miss_distance=0.35,
                radial=0.1,
                in_track=0.2,
                cross_track=0.3,
                pc=2.3e-4,
                covariance_matrix={
                    "p_cov": [[0.1, 0.0, 0.0], [0.0, 0.1, 0.0], [0.0, 0.0, 0.1]],
                    "s_cov": [[0.15, 0.0, 0.0], [0.0, 0.15, 0.0], [0.0, 0.0, 0.15]]
                },
                compliance_status="Nominal"
            )
            reentry = ReentryAlert(
                norad_id=25544,
                name="ISS (ZARYA)",
                current_altitude=285.5,
                decay_rate=12.5,
                eta=datetime.now(timezone.utc) + timedelta(days=3),
                uncertainty_hours=6.0,
                survival_pct=15.0,
                casualty_probability=1.2e-5,
                corridor_geom='{"type": "LineString", "coordinates": [[0,0], [1,1]]}'
            )
            session.add_all([iss, sec, event, reentry])
            await session.commit()

    asyncio.run(_init())
    yield
    
    app.dependency_overrides.pop(get_db, None)
    asyncio.run(engine.dispose())
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

def test_conjunction_explain_metrics():
    """
    Verifies that the GET /api/conjunctions/{event_id} details endpoint returns
    the detailed explainable Pc mathematical telemetry fields.
    """
    # Query endpoint
    response = client.get("/api/conjunctions/1")
    assert response.status_code == 200
    data = response.json()
    
    # Verify explainable math telemetry
    assert "explain" in data
    explain = data["explain"]
    assert "miss_distance_km" in explain
    assert "sigma_major" in explain
    assert "sigma_minor" in explain
    assert "pc_terms" in explain
    assert "u" in explain["pc_terms"]

def test_solar_forecast_endpoint():
    """
    Verifies that the GET /api/solar/forecast endpoint returns the solar threat
    level and multiplier.
    """
    response = client.get("/api/solar/forecast")
    assert response.status_code == 200
    data = response.json()
    assert "overall_threat" in data
    assert "density_multiplier" in data
    assert "f10_7" in data
    assert "ap" in data

def test_satellite_plain_language_risk_report():
    """
    Verifies that the GET /api/satellites/{norad_id}/risk-report endpoint returns
    a plain-language summary of conjunction, reentry, and compliance risks.
    """
    response = client.get("/api/satellites/25544/risk-report")
    assert response.status_code == 200
    data = response.json()
    
    assert data["norad_id"] == 25544
    assert "plain_language_explanation" in data
    assert "ISS (ZARYA)" in data["plain_language_explanation"]
    assert "decay" in data["plain_language_explanation"].lower()
    assert data["risk_metrics"]["reentry_risk"] == "HIGH"

def test_satellite_tle_import_and_screening():
    """
    Verifies that POST /api/satellites/import successfully accepts standard TLEs,
    propagates the satellite forwards, and screens against existing states.
    """
    # Post raw TLE payload
    tle_payload = {
        "name": "MOCK-IMPORT-SAT",
        "tle1": "1 99991U 26001A   26180.12345678  .00000000  00000-0  00000-0 0  9993",
        "tle2": "2 99991  98.2000 120.3000 0001000   0.0000   0.0000 14.50000000  9994"
    }
    
    # 1. Verify details don't exist yet
    response = client.get("/api/satellites/99991/details")
    assert response.status_code == 404
    
    # 2. Import satellite
    response = client.post("/api/satellites/import", json=tle_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["norad_id"] == 99991
    assert data["name"] == "MOCK-IMPORT-SAT"
    
    # 3. Verify details now exist
    response = client.get("/api/satellites/99991/details")
    assert response.status_code == 200
    assert response.json()["norad_id"] == 99991

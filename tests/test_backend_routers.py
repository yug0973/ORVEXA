import os
import json
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Set Database URL to test SQLite before importing app
TEST_DB_FILE = "test_ORVEXA_backend.db"
if os.path.exists(TEST_DB_FILE):
    try:
        os.remove(TEST_DB_FILE)
    except Exception:
        pass

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_FILE}"

from backend.main import app
from backend.db.models import Base, Satellite, StateVector, ConjunctionEvent, ReentryAlert

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    """
    Setup temporary test SQLite database with mock data.
    """
    import asyncio
    test_db_url = f"sqlite+aiosqlite:///{TEST_DB_FILE}"
    engine = create_async_engine(test_db_url, echo=False)
    
    async def _init():
        # 1. Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            
        AsyncSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # 2. Insert mock seed data
        async with AsyncSessionLocal() as session:
            sat1 = Satellite(
                norad_id=25544,
                name="ISS (ZARYA)",
                operator="NASA/ROSCOSMOS",
                type="Payload",
                tle1="1 25544U 98067A   20351.52044444  .00001000  00000-0  26000-4 0  9998",
                tle2="2 25544  51.6467  44.5727 0002164  73.9623  34.8726 15.49280000260408",
                updated_at=datetime.now(timezone.utc)
            )
            sat2 = Satellite(
                norad_id=900,
                name="CALSPHERE 1",
                operator="US Navy",
                type="Calibration",
                tle1="1 00900U 64063C   20351.52044444  .00001000  00000-0  26000-4 0  9998",
                tle2="2 00900  90.0000 120.0000 0001000  45.0000 270.0000 14.50000000000000",
                updated_at=datetime.now(timezone.utc)
            )
            session.add_all([sat1, sat2])
            await session.flush()
            
            sv = StateVector(
                norad_id=25544,
                epoch=datetime.now(timezone.utc),
                position_x=1200.0, position_y=2300.0, position_z=3400.0,
                velocity_x=7.1, velocity_y=1.5, velocity_z=-2.2
            )
            session.add(sv)
            
            conj = ConjunctionEvent(
                primary_norad=25544,
                secondary_norad=900,
                tca=datetime.now(timezone.utc),
                miss_distance=0.35,
                radial=0.01,
                in_track=0.25,
                cross_track=-0.24,
                pc=1.2e-4,
                covariance_matrix={"p_cov": [[1,0],[0,1]]},
                compliance_status="Compliance Required"
            )
            session.add(conj)
            
            alert = ReentryAlert(
                norad_id=900,
                name="CALSPHERE 1",
                current_altitude=130.0,
                decay_rate=0.1,
                eta=datetime.now(timezone.utc),
                uncertainty_hours=0.5,
                survival_pct=5.0,
                corridor_geom="POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))",
                casualty_probability=0.0001
            )
            session.add(alert)
            await session.commit()

    asyncio.run(_init())
    yield
    asyncio.run(engine.dispose())
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

def test_api_root():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "online"

def test_get_satellites():
    res = client.get("/api/satellites?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["results"]) == 2
    names = [r["name"] for r in data["results"]]
    assert "ISS (ZARYA)" in names
    assert "CALSPHERE 1" in names

def test_get_satellites_search():
    res = client.get("/api/satellites?search=US%20Navy")
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "CALSPHERE 1"

def test_get_trajectory():
    res = client.get("/api/satellites/25544/trajectory")
    assert res.status_code == 200
    data = res.json()
    assert data["norad_id"] == 25544
    assert len(data["trajectory"]) == 1
    assert data["trajectory"][0]["position"] == [1200.0, 2300.0, 3400.0]

def test_get_czml():
    res = client.get("/api/satellites/czml?limit=2")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["id"] == "document"
    assert "clock" in data[0]

def test_get_conjunctions():
    res = client.get("/api/conjunctions")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["primary_norad"] == 25544
    assert data[0]["primary_name"] == "ISS (ZARYA)"
    assert data[0]["secondary_name"] == "CALSPHERE 1"
    
def test_get_conjunction_details():
    # Since it's the first event, the ID is 1
    res = client.get("/api/conjunctions/1")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 1
    assert data["pc"] == 1.2e-4
    assert data["relative_vectors"]["radial"] == 0.01

def test_get_reentry():
    res = client.get("/api/reentry")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["name"] == "CALSPHERE 1"

def test_get_reentry_map():
    res = client.get("/api/reentry/900/map")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
    assert data["features"][0]["geometry"]["type"] == "Polygon"
    assert data["features"][0]["properties"]["name"] == "CALSPHERE 1"

def test_get_solar():
    res = client.get("/api/solar")
    assert res.status_code == 200
    data = res.json()
    assert "current" in data
    assert "alert_metrics" in data
    assert len(data["trend_history"]) == 7


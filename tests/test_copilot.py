import os
import json
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

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
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            
        AsyncSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with AsyncSessionLocal() as session:
            sat = Satellite(
                norad_id=25544,
                name="ISS (ZARYA)",
                operator="NASA/ROSCOSMOS",
                type="Payload",
                tle1="1 25544U 98067A   20351.52044444  .00001000  00000-0  26000-4 0  9998",
                tle2="2 25544  51.6467  44.5727 0002164  73.9623  34.8726 15.49280000260408",
                updated_at=datetime.now(timezone.utc)
            )
            session.add(sat)
            
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
                norad_id=25544,
                name="ISS (ZARYA)",
                current_altitude=130.0,
                decay_rate=12.5,
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

def test_copilot_chat_offline_fallback():
    """
    Verify that querying the copilot router returns success status,
    and fallback is triggered with correct satellite details if Ollama is unreachable.
    """
    payload = {
        "message": "What is the status of ISS (ZARYA)? Also check for close approach and reentry.",
        "history": []
    }
    
    res = client.post("/api/copilot/chat", json=payload)
    assert res.status_code == 200
    
    data = res.json()
    assert data["status"] == "success"
    assert "response" in data
    assert "mode" in data
    
    # If the local Ollama is offline (common in CI/test environments), verify fallback contents
    if data["mode"] == "offline":
        response_text = data["response"]
        assert "Offline Assistant Telemetry Report" in response_text
        assert "ISS (ZARYA)" in response_text
        assert "NASA/ROSCOSMOS" in response_text
        assert "Conjunction" in response_text or "Approach" in response_text
        assert "Reentry" in response_text or "Decay" in response_text

import os
import json
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Set database environment to temporary SQLite for routers import
TEST_DB_FILE = "test_ORVEXA_backend.db"
if os.path.exists(TEST_DB_FILE):
    try:
        os.remove(TEST_DB_FILE)
    except Exception:
        pass

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_FILE}"

from backend.main import app
from backend.db.models import Base, Satellite, ConjunctionEvent, ComplianceFiling
from backend.services.compliance_generator import generate_compliance_brief, compile_pdf_document

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    """
    Setup temporary test SQLite database with seed conjunction data.
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
            sat = Satellite(
                norad_id=25544,
                name="ISS (ZARYA)",
                operator="NASA/ROSCOSMOS",
                type="Payload",
                tle1="1 25544U...",
                tle2="2 25544...",
                updated_at=datetime.now(timezone.utc)
            )
            session.add(sat)
            await session.flush()
            
            conj = ConjunctionEvent(
                id=123,
                primary_norad=25544,
                secondary_norad=900,
                tca=datetime.now(timezone.utc),
                miss_distance=0.45,
                radial=0.01,
                in_track=0.25,
                cross_track=-0.24,
                pc=1.2e-4,
                covariance_matrix={"p_cov": [[1,0],[0,1]]},
                compliance_status="Compliance Required"
            )
            session.add(conj)
            await session.commit()

    asyncio.run(_init())
    yield
    asyncio.run(engine.dispose())
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

def test_generate_compliance_brief_fallback():
    """
    Verify the fallback briefing generator builds a valid structured text description.
    """
    event_data = {
        "primary_name": "ISS (ZARYA)",
        "primary_norad": 25544,
        "secondary_name": "CALSPHERE 1",
        "secondary_norad": 900,
        "tca": "2026-08-09T12:00:00",
        "miss_distance": 0.45,
        "pc": 1.2e-4,
        "operator_name": "SpaceOps India"
    }
    
    brief = generate_compliance_brief(event_data)
    assert isinstance(brief, str)
    assert len(brief) > 50
    assert "ISS (ZARYA)" in brief or "ISS" in brief or "ZARYA" in brief

def test_compile_pdf_document():
    """
    Verify the ReportLab engine successfully compiles a valid, non-empty PDF document on disk.
    """
    filing_data = {
        "id": 9999,
        "satellite": "ISS (ZARYA)",
        "primary_norad": 25544,
        "secondary_norad": 900,
        "operator": "SpaceOps India",
        "tca": datetime.now(),
        "status": "Filed",
        "submitted_at": datetime.now(),
        "briefing": "Mock briefing text explaining collision risk mitigation."
    }
    
    pdf_path = compile_pdf_document(filing_data)
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 0
    
    # Clean up the generated file
    try:
        os.remove(pdf_path)
    except Exception:
        pass

def test_post_file_compliance_endpoint():
    """
    Verify the POST /api/compliance/file endpoint creates database records,
    triggers PDF compilation, and returns correct metadata.
    """
    payload = {
        "event_id": "123",
        "operator_name": "NASA/ROSCOSMOS Operator"
    }
    
    res = client.post("/api/compliance/file", json=payload)
    assert res.status_code == 201
    
    data = res.json()
    assert "id" in data
    assert data["operator"] == "NASA/ROSCOSMOS Operator"
    assert data["status"] == "Filed"
    assert "pdf_path" in data
    assert os.path.exists(data["pdf_path"])
    
    # Save the filing ID for download test
    pytest.test_filing_id = data["id"]
    pytest.test_pdf_path = data["pdf_path"]

def test_get_download_compliance_endpoint():
    """
    Verify GET /api/compliance/download/{filing_id} successfully serves
    the generated print-ready PDF binary stream.
    """
    filing_id = getattr(pytest, "test_filing_id", None)
    assert filing_id is not None
    
    res = client.get(f"/api/compliance/download/{filing_id}")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) > 0
    
    # Clean up the test PDF file generated
    pdf_path = getattr(pytest, "test_pdf_path", None)
    if pdf_path and os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except Exception:
            pass
            
def test_get_download_not_found():
    """
    Verify download endpoint throws 404 for invalid filing IDs.
    """
    res = client.get("/api/compliance/download/999999")
    assert res.status_code == 404

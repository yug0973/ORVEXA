import os
# Set database URL to SQLite before importing models to trigger fallback schema
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_backend_ORVEXA.db"

import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.db.models import Base, Satellite, StateVector, ConjunctionEvent, ReentryAlert, ComplianceFiling

@pytest.mark.asyncio
async def test_async_db_setup_and_insert():
    """
    Asynchronously test table creation, session management, insertion,
    and querying for all backend ORM models under SQLite fallback.
    """
    test_db_file = "test_backend_ORVEXA.db"
    
    if os.path.exists(test_db_file):
        try:
            os.remove(test_db_file)
        except Exception:
            pass
            
    test_db_url = f"sqlite+aiosqlite:///{test_db_file}"
    
    # Configure test async database engine
    engine = create_async_engine(test_db_url, echo=False)
    
    try:
        # 1. Create tables asynchronously
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        # Define async session factory
        AsyncSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # 2. Insert records using the async session
        async with AsyncSessionLocal() as session:
            # Insert Satellite
            sat = Satellite(
                norad_id=25544,
                name="ISS (ZARYA)",
                operator="NASA/ROSCOSMOS",
                type="Payload",
                tle1="1 25544U 98067A   20351.52044444  .00001000  00000-0  26000-4 0  9998",
                tle2="2 25544  51.6467  44.5727 0002164  73.9623  34.8726 15.49280000260408",
                updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            session.add(sat)
            await session.flush()  # Flush so foreign key constraints are satisfied
            
            # Insert StateVector
            sv = StateVector(
                norad_id=25544,
                epoch=datetime.now(timezone.utc).replace(tzinfo=None),
                position_x=1234.56,
                position_y=-4567.89,
                position_z=3210.12,
                velocity_x=7.5,
                velocity_y=1.2,
                velocity_z=-2.4
            )
            session.add(sv)
            
            # Insert ConjunctionEvent
            conj = ConjunctionEvent(
                primary_norad=25544,
                secondary_norad=25544,  # Self-conjunction representation for test
                tca=datetime.now(timezone.utc).replace(tzinfo=None),
                miss_distance=0.45,
                radial=0.05,
                in_track=-0.42,
                cross_track=0.15,
                pc=3.4e-5,
                covariance_matrix={"matrix": [[1.2, 0.0], [0.0, 0.85]]},
                compliance_status="Pending"
            )
            session.add(conj)
            
            # Insert ReentryAlert (using text-based GIS representation for SQLite fallback)
            alert = ReentryAlert(
                norad_id=25544,
                name="ISS (ZARYA)",
                current_altitude=120.5,
                decay_rate=0.12,
                eta=datetime.now(timezone.utc).replace(tzinfo=None),
                uncertainty_hours=0.25,
                survival_pct=45.0,
                corridor_geom="POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))",
                casualty_probability=0.00018
            )
            session.add(alert)
            
            # Insert ComplianceFiling
            filing = ComplianceFiling(
                operator="NASA/ROSCOSMOS",
                satellite="ISS (ZARYA)",
                tca=datetime.now(timezone.utc).replace(tzinfo=None),
                form_data={"jurisdiction": "UN", "liability_agreement": True},
                pdf_path="/docs/compliance/filing_25544.pdf",
                status="Approved",
                submitted_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            session.add(filing)
            
            await session.commit()
            
        # 3. Query and Verify records asynchronously
        async with AsyncSessionLocal() as session:
            import sqlalchemy as sa
            
            # Verify Satellite
            res = await session.execute(sa.select(Satellite).filter_by(norad_id=25544))
            db_sat = res.scalar_one_or_none()
            assert db_sat is not None
            assert db_sat.name == "ISS (ZARYA)"
            
            # Verify StateVector relation
            res_sv = await session.execute(sa.select(StateVector).filter_by(norad_id=25544))
            db_sv = res_sv.scalar_one_or_none()
            assert db_sv is not None
            assert db_sv.position_x == 1234.56
            
            # Verify ConjunctionEvent
            res_conj = await session.execute(sa.select(ConjunctionEvent).filter_by(primary_norad=25544))
            db_conj = res_conj.scalar_one_or_none()
            assert db_conj is not None
            assert db_conj.pc == 3.4e-5
            assert db_conj.covariance_matrix == {"matrix": [[1.2, 0.0], [0.0, 0.85]]}
            
            # Verify ReentryAlert
            res_alert = await session.execute(sa.select(ReentryAlert).filter_by(norad_id=25544))
            db_alert = res_alert.scalar_one_or_none()
            assert db_alert is not None
            assert db_alert.corridor_geom == "POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))"
            
            # Verify ComplianceFiling
            res_filing = await session.execute(sa.select(ComplianceFiling).filter_by(status="Approved"))
            db_filing = res_filing.scalar_one_or_none()
            assert db_filing is not None
            assert db_filing.operator == "NASA/ROSCOSMOS"
            assert db_filing.form_data == {"jurisdiction": "UN", "liability_agreement": True}
            
    finally:
        # Clean up database connection and file
        await engine.dispose()
        if os.path.exists(test_db_file):
            try:
                os.remove(test_db_file)
            except Exception:
                pass

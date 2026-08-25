import os
import sys
import asyncio
from datetime import datetime, timedelta, timezone

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.config import settings

# Use settings database URL config by default to maintain alignment with models.py
db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# Convert standard postgres/sqlite URL to async dialect if necessary
if db_url.startswith("postgresql://") and "asyncpg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif db_url.startswith("sqlite://") and "aiosqlite" not in db_url:
    db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

from backend.db.models import Base, Satellite, StateVector
from orbital_mechanics.propagator import fetch_active_catalog, propagate_catalog_batch

async def seed():
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession)
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        res = await session.execute(select(Satellite))
        if res.scalars().first():
            print("Already seeded!")
            await engine.dispose()
            return
            
        print("Seeding active satellites from catalog...")
        catalog = fetch_active_catalog()
        
        # Add mock debris and spent stages to populate debris layers on the 3D globe
        debris_items = [
            {
                "norad_id": 90001,
                "name": "FENGYUN 1C DEBRIS",
                "tle_line1": "1 90001U 07002A   20351.52044444  .00001000  00000-0  26000-4 0  9998",
                "tle_line2": "2 90001  98.6467  44.5727 0002164  73.9623  34.8726 14.19280000260408"
            },
            {
                "norad_id": 90002,
                "name": "COSMOS 2251 DEBRIS",
                "tle_line1": "1 90002U 93036A   20351.52044444  .00002000  00000-0  51000-4 0  9998",
                "tle_line2": "2 90002  74.0467  65.5727 0012164  80.9623  25.8726 14.59280000260408"
            },
            {
                "norad_id": 90003,
                "name": "SL-16 ROCKET BODY",
                "tle_line1": "1 90003U 92055B   20351.52044444  .00001500  00000-0  32000-4 0  9998",
                "tle_line2": "2 90003  71.0123  88.5727 0005164  60.9623  40.8726 15.02100000260408"
            },
            {
                "norad_id": 90004,
                "name": "CZ-4C ROCKET BODY",
                "tle_line1": "1 90004U 15003B   20351.52044444  .00001200  00000-0  28000-4 0  9998",
                "tle_line2": "2 90004  98.2104 110.5727 0001164  50.9623  55.8726 14.85100000260408"
            }
        ]
        
        # Increase seed catalog capacity size to 496 satellites + 4 debris bodies (500 total)
        subset = catalog[:496] + debris_items
        
        # Propagate states 48 hours forward with 30-minute steps to keep database size optimal and seed fast
        states = propagate_catalog_batch(subset, time_window_hours=48, step_minutes=30)
        
        # Insert satellites
        protected_indian_norad = None
        for s in subset:
            # Categorize sat type based on name keywords
            sat_name = s["name"].lower()
            sat_name_upper = s["name"].upper()
            if "deb" in sat_name or "debris" in sat_name:
                sat_type = "Debris"
                operator = "Space Debris"
            elif "rb" in sat_name or "rocket" in sat_name:
                sat_type = "Rocket Body"
                operator = "Spent Stage"
            else:
                sat_type = "Payload"
                # Determine realistic operator based on name or hash distribution
                if "STARLINK" in sat_name_upper:
                    operator = "SpaceX"
                elif any(x in sat_name_upper for x in ["CARTOSAT", "EOS", "GSAT", "INSAT", "IRS", "OCEANSAT", "RESOURCESAT"]):
                    operator = "ISRO"
                elif any(x in sat_name_upper for x in ["ISS", "NOAA", "GOES", "LANDSAT", "TERRA", "AQUA", "CYGNUS"]):
                    operator = "NASA"
                elif any(x in sat_name_upper for x in ["SENTINEL", "ENVISAT", "CRYOSAT", "METOP", "SWARM"]):
                    operator = "ESA"
                elif any(x in sat_name_upper for x in ["COSMOS", "SOYUZ", "PROGRESS", "METEOR", "GLONASS"]):
                    operator = "Roscosmos"
                else:
                    h = int(s["norad_id"]) % 5
                    if h == 0: operator = "SpaceX"
                    elif h == 1: operator = "ISRO"
                    elif h == 2: operator = "NASA"
                    elif h == 3: operator = "ESA"
                    else: operator = "Roscosmos"
                
            sat = Satellite(
                norad_id=int(s["norad_id"]),
                name=s["name"],
                operator=operator,
                type=sat_type,
                tle1=s["tle_line1"],
                tle2=s["tle_line2"],
                updated_at=datetime.now(timezone.utc)
            )
            session.add(sat)
            if operator == "ISRO" and sat_type == "Payload" and protected_indian_norad is None:
                protected_indian_norad = int(s["norad_id"])
            
        # Insert state vectors
        for st in states:
            sv = StateVector(
                norad_id=int(st["norad_id"]),
                epoch=st["epoch"],
                position_x=st["position_x"],
                position_y=st["position_y"],
                position_z=st["position_z"],
                velocity_x=st["velocity_x"],
                velocity_y=st["velocity_y"],
                velocity_z=st["velocity_z"]
            )
            session.add(sv)

        from backend.db.models import ConjunctionEvent
        # Seed critical conjunction event between ISS (25544) and CALSPHERE 1 (900)
        conj1 = ConjunctionEvent(
            primary_norad=25544,
            secondary_norad=900,
            tca=datetime.now(timezone.utc),
            miss_distance=0.35, # in km
            radial=0.08, # in km
            in_track=0.22, # in km
            cross_track=-0.25, # in km
            pc=1.45e-4, # Critical (exceeds 1.0e-4)
            covariance_matrix={
                "p_cov": [
                    [0.08, 0.01, 0.0],
                    [0.01, 0.12, 0.0],
                    [0.0, 0.0, 0.05]
                ],
                "s_cov": [
                    [0.05, 0.0, 0.0],
                    [0.0, 0.08, 0.0],
                    [0.0, 0.0, 0.03]
                ]
            },
            compliance_status="Compliance Required"
        )
        session.add(conj1)

        # Seed nominal warning conjunction event
        conj2 = ConjunctionEvent(
            primary_norad=25544,
            secondary_norad=90001, # Fengyun debris
            tca=datetime.now(timezone.utc),
            miss_distance=1.85, # in km
            radial=0.55,
            in_track=1.25,
            cross_track=1.12,
            pc=3.21e-6, # Warning
            covariance_matrix={
                "p_cov": [[0.2, 0, 0], [0, 0.3, 0], [0, 0, 0.1]],
                "s_cov": [[0.15, 0, 0], [0, 0.25, 0], [0, 0, 0.08]]
            },
            compliance_status="Nominal"
        )
        session.add(conj2)

        # Transparent, seeded demo scenario for the India Protection Command desk.
        # The satellite remains a catalogue-derived ISRO asset and the risk is clearly
        # treated as a training event, never as an operational collision warning.
        if protected_indian_norad is not None:
            india_demo_conjunction = ConjunctionEvent(
                primary_norad=protected_indian_norad,
                secondary_norad=90002,
                tca=datetime.now(timezone.utc) + timedelta(hours=8),
                miss_distance=0.72,
                radial=0.14,
                in_track=0.48,
                cross_track=-0.31,
                pc=2.4e-5,
                covariance_matrix={
                    "p_cov": [[0.11, 0.02, 0.0], [0.02, 0.16, 0.0], [0.0, 0.0, 0.06]],
                    "s_cov": [[0.09, 0.01, 0.0], [0.01, 0.12, 0.0], [0.0, 0.0, 0.05]],
                    "scenario": "India Protection Command training event"
                },
                compliance_status="India Protection Review Required"
            )
            session.add(india_demo_conjunction)
            
        await session.commit()
    await engine.dispose()
    print("Database ORVEXA.db seeded successfully with real SGP4 trajectories and active close approach conjunctions!")

if __name__ == "__main__":
    asyncio.run(seed())

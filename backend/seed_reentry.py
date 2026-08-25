import os
import sys
import json
import asyncio
from datetime import datetime, timezone, timedelta

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from backend.config import settings

# Use settings database URL config by default to maintain alignment with models.py
db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# Convert standard postgres/sqlite URL to async dialect if necessary
if db_url.startswith("postgresql://") and "asyncpg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif db_url.startswith("sqlite://") and "aiosqlite" not in db_url:
    db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

from backend.db.models import Base, ReentryAlert, Satellite

async def seed():
    engine = create_async_engine(db_url)
    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession)
    
    async with AsyncSessionLocal() as session:
        # Check if satellites exist
        res = await session.execute(select(Satellite))
        sats = res.scalars().all()
        if not sats:
            print("No satellites found! Run the main seeder first.")
            await engine.dispose()
            return
            
        # Check if already has reentry alerts
        check = await session.execute(select(ReentryAlert))
        if check.scalars().first():
            print("Reentry alerts already seeded.")
            await engine.dispose()
            return
            
        print("Seeding reentry alerts...")
        
        # We will add reentry alerts for the first 2 satellites in the database
        target_sats = sats[:2]
        
        # Corridor 1: Centered on Indian Ocean / Bay of Bengal
        corridor1 = {
          "type": "Polygon",
          "coordinates": [
            [[65.0, 5.0], [88.0, 7.0], [85.0, 18.0], [62.0, 16.0], [65.0, 5.0]]
          ]
        }
        
        # Corridor 2: Centered on South Pacific Ocean
        corridor2 = {
          "type": "Polygon",
          "coordinates": [
            [[-140.0, -45.0], [-115.0, -42.0], [-120.0, -32.0], [-145.0, -35.0], [-140.0, -45.0]]
          ]
        }
        
        alerts = [
            ReentryAlert(
                norad_id=target_sats[0].norad_id,
                name=target_sats[0].name,
                current_altitude=185.4,
                decay_rate=12.45,
                eta=datetime.now(timezone.utc) + timedelta(days=2, hours=4),
                uncertainty_hours=6.5,
                survival_pct=18.5,
                corridor_geom=json.dumps(corridor1),
                casualty_probability=1.25e-5
            ),
            ReentryAlert(
                norad_id=target_sats[1].norad_id,
                name=target_sats[1].name,
                current_altitude=198.2,
                decay_rate=8.12,
                eta=datetime.now(timezone.utc) + timedelta(days=3, hours=12),
                uncertainty_hours=12.0,
                survival_pct=24.0,
                corridor_geom=json.dumps(corridor2),
                casualty_probability=3.85e-6
            )
        ]
        
        for alert in alerts:
            session.add(alert)
            
        await session.commit()
    await engine.dispose()
    print("Reentry alerts seeded successfully into ORVEXA.db!")

if __name__ == "__main__":
    asyncio.run(seed())

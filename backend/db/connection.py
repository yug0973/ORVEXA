import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from backend.config import settings

# 1. Retrieve the Database connection string from environment or settings
DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# Convert synchronous connection schemas to their asynchronous counterparts
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("sqlite://"):
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)

# Configure extra connection arguments for SQLite fallback compatibility
connect_args = {}
if "sqlite" in DATABASE_URL.lower():
    connect_args["check_same_thread"] = False

# 2. Create the asynchronous SQLAlchemy engine
engine = create_async_engine(DATABASE_URL, connect_args=connect_args, echo=False)

# 3. Setup the async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 4. Dependency injection session provider for FastAPI routers
async def get_db():
    """
    Asynchronous database session generator dependency.
    Yields an active database session and ensures commit/rollback safety.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

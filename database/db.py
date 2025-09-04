from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from utils.config import DATABASE_URL

# Create async engine
engine = create_async_engine(
    DATABASE_URL, 
    echo=False,  # Production da False qiling
    pool_pre_ping=True,
    pool_recycle=300
)

# Base class for models
Base = declarative_base()

# Async session factory
async_session = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_session() -> AsyncSession: # type: ignore
    """Provide a new async database session"""
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

# Database initialization
async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """Close database connection"""
    await engine.dispose()
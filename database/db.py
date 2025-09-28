from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from utils.config import DATABASE_URL

# 🔹 Base class for models
Base = declarative_base()

# 🔹 Async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,          
    pool_pre_ping=True,
    pool_recycle=300
)

# 🔹 Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 🔹 Session generator
async def get_session() -> AsyncSession:  
    """Har safar yangi session qaytaradi"""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Bazadagi barcha jadvalni yaratish"""
    async with engine.begin() as conn:
        from . import models
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Bazaga ulanishni yopish"""
    await engine.dispose()

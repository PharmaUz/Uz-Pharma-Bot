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
    """
    Asynchronously provides a new SQLAlchemy AsyncSession instance.

    Yields:
        AsyncSession: A new asynchronous database session.

    Raises:
        Exception: Propagates any exception that occurs during session usage after rolling back the transaction.

    Ensures:
        The session is properly closed after use, and any transaction is rolled back if an exception occurs.
    """
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initializes the database by creating all tables defined in the application's models.

    This asynchronous function establishes a connection to the database engine and creates all tables
    based on the metadata from the imported models. It should be called at application startup to ensure
    that the database schema is up to date.

    Raises:
        Any exceptions raised by the database engine during table creation.
    """
    async with engine.begin() as conn:
        from . import models
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Asynchronously closes the database connection by disposing of the engine.

    This function should be called when the application is shutting down or when
    the database connection is no longer needed to ensure that all resources are
    properly released.
    """
    await engine.dispose()

import sqlite3
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from utils.config import DATABASE_URL

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Base class for models
Base = declarative_base()

# Async session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncSession:
    """Provide a new async database session"""
    async with async_session() as session:
        yield session


def init_db():
    conn = sqlite3.connect("comments.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        user_id INTEGER,
        username TEXT,
        description TEXT,
        is_approved INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()
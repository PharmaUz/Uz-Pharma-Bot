import asyncio
import os
from dotenv import load_dotenv

from loader import bot, dp
from handlers import start, cooperation, feedback, filter, order
from handlers.admin.router import router as admin_router

from users import pharmacy
from database.db import engine, Base

# Load .env
load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID"))


# Connect routers
dp.include_router(start.router)
dp.include_router(cooperation.router)
dp.include_router(feedback.router)
dp.include_router(filter.router)
dp.include_router(order.router)
dp.include_router(pharmacy.router)
dp.include_router(admin_router)


async def create_tables():
    """Create database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main():
    # Create database tables
    await create_tables()
    print("✅ Database tables created")

    # Start the bot
    print("🤖 Bot started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

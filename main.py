import asyncio
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from handlers import start, cooperation, feedback, filter
from database.db import engine, Base

# Load .env
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Connect routers
dp.include_router(start.router)
dp.include_router(cooperation.router)
dp.include_router(feedback.router)
dp.include_router(filter.router)

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


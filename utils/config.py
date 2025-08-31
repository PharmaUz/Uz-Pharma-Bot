import os
from dotenv import load_dotenv

load_dotenv()

# Database - for PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://pharma_user:pharma_9878@localhost:5432/pharma_bot")

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

import os
from dotenv import load_dotenv

load_dotenv()

# Database - for PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://pharma_user:pharma_9878@localhost:5432/pharma_bot")

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Redis URL (agar kerak bo'lsa)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# File upload settings
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB

# Pagination
DRUGS_PER_PAGE = int(os.getenv("DRUGS_PER_PAGE", 10))

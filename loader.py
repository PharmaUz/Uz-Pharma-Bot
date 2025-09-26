# loader.py
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("BOT_TOKEN .env faylda topilmadi!")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

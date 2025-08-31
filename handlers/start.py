from aiogram import Router, types
from aiogram.filters import Command
from keyboards.main_menu import get_main_menu

router = Router()


@router.message(Command("start"))
async def start_handler(message: types.Message):
    """
    Handle the /start command.

    Greets the user by username (or full name if username is not set)
    and shows the main menu.
    """
    username = message.from_user.username or message.from_user.full_name
    await message.answer(f"Salom, {username} 👋", reply_markup=get_main_menu())

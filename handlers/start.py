from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.main_menu import get_main_menu

from handlers.cooperation import ADMIN_ID  # Import ADMIN_ID from handlers.cooperation

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



@router.message(F.text.startswith("/"))
async def comment(message: types.Message):
    """
    Handle unknown commands.

    Informs the user that the command is not recognized
    and suggests using the main menu.
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    order_id = "12345" # we'll write it down by hand for now
    comment_text = message.text


    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Qabul qilish", callback_data=f"confirm_comment:{order_id}:{user_id}"),
                InlineKeyboardButton(text="Bekor qilish", callback_data=f"cancel_comment:{order_id}:{user_id}")
            ]
        ]
    )

    await message.bot.send_message(
        ADMIN_ID,
        f"🆔 Order ID: {order_id}\n👤 User: @{username}\n💬 {comment_text}",
        reply_markup=keyboard
    )
    await message.answer("❓ Noma'lum buyruq. Iltimos, asosiy menyudan foydalaning.", reply_markup=get_main_menu())
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards import get_main_menu, get_pharmacy_menu
from sqlalchemy import select
from database.models import Pharmacy
from database.db import async_session

from handlers.cooperation import ADMIN_ID

router = Router()

@router.message(Command("start"))
async def start_handler(message: types.Message):
    """
    Handle the /start command.

    Greets the user by username (or full name if username is not set)
    and shows the main menu.
    """
    async with async_session() as session:
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.full_name

        result = await session.execute(
            select(Pharmacy).where(Pharmacy.tg_id == user_id)
        )
        pharmacy = result.scalar_one_or_none()

        if pharmacy:
            await message.answer(
                f"Salom, {pharmacy.name} dorixonasi! 🏥\n\n"
                f"Sizning dorixonangiz: {pharmacy.name}\n"
                f"Manzil: {pharmacy.address or 'Korsatilmagan'}\n\n"
                f"Quyidagi tugmalar orqali buyurtmalarni boshqaring:",
                reply_markup=get_pharmacy_menu()
            )
        else:
            await message.answer(f"Salom, {username} 👋", reply_markup=get_main_menu())


@router.message(F.text.startswith("/"))
async def comment(message: types.Message):
    """
    Handle unknown or unrecognized commands entered by users.
    Sends the message to the admin for review.
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    order_id = "12345"  # temporary placeholder
    comment_text = message.text

    # Buttons for admin to confirm or reject the message
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Qabul qilish", callback_data=f"confirm_comment:{order_id}:{user_id}"),
                InlineKeyboardButton(text="Bekor qilish", callback_data=f"cancel_comment:{order_id}:{user_id}")
            ]
        ]
    )

    # Send message to admin
    await message.bot.send_message(
        ADMIN_ID,
        f"🆔 Order ID: {order_id}\n👤 User: @{username}\n💬 {comment_text}",
        reply_markup=keyboard,
    )
    await message.answer(
        "❓ Noma'lum buyruq. Iltimos, asosiy menyudan foydalaning.", 
        reply_markup=get_main_menu()
    )
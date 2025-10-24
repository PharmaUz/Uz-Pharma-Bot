from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove
)
from keyboards import get_main_menu, get_pharmacy_menu
from sqlalchemy import select
from database.models import Pharmacy, User, UserStatus
from database.db import async_session

from handlers.cooperation import ADMIN_ID

router = Router()

@router.message(Command("start"))
async def start_handler(message: types.Message):
    """
    Handle the /start command.

    Greets the user by username (or full name if username is not set),
    asks for their phone number, and shows the appropriate menu based on user status.
    """
    async with async_session() as session:
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.full_name

        # Check if the user already exists
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            # Ask for phone number
            phone_button = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            await message.answer(
                f"Salom, {username} 👋\n\nIltimos, telefon raqamingizni yuboring:",
                reply_markup=phone_button
            )
        else:
            if existing_user.status == UserStatus.PHARMACY_ADMIN.value:
                await message.answer(
                    f"Salom, {username} 👋\n\nSiz dorixona admini sifatida tizimga kirdingiz!",
                    reply_markup=get_pharmacy_menu()
                )
            else:
                await message.answer(
                    f"Salom, {username} 👋\n\nSiz allaqachon ro'yxatdan o'tgansiz!",
                    reply_markup=get_main_menu()
                )


@router.message(F.contact)
async def save_user_contact(message: types.Message):
    """
    Save the user's phone number and other details to the database.
    """
    async with async_session() as session:
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.full_name
        fullname = message.from_user.full_name
        phone_number = message.contact.phone_number

        # Save user to the database
        new_user = User(
            telegram_id=user_id,
            username=username,
            fullname=fullname,
            phone_number=phone_number,
            status=UserStatus.REGULAR.value  # Use the lowercase string value of the enum
        )
        session.add(new_user)
        await session.commit()

        await message.answer(
            "Rahmat! Telefon raqamingiz saqlandi. Endi asosiy menyudan foydalanishingiz mumkin.",
            reply_markup=get_main_menu()
        )

        # Remove the phone number request button
        await message.answer(
            "Telefon raqamingiz qabul qilindi.",
            reply_markup=ReplyKeyboardRemove()
        )


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
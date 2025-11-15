from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove
)
from keyboards import get_main_menu, get_pharmacy_menu
from keyboards.admin_menu import admin_main_menu
from sqlalchemy import select
from database.models import Pharmacy, User, UserStatus
from database.db import async_session
from os import getenv
from sqlalchemy.exc import IntegrityError
from aiogram.fsm.state import State, StatesGroup

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
        print(user_id)
        # Check if the user is the admin
        if user_id == ADMIN_ID:
            await message.answer(
                f"Salom, {username} 👋\n\nSiz admin sifatida tizimga kirdingiz!\nBu qisim keyingi versiyalar uchun, to'liq emas, kamchiliklar bor 📈",
                reply_markup=admin_main_menu()
            )
            return

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
            # Check if the user is a pharmacy admin by tg_id
            pharmacy_admin = await session.execute(
                select(Pharmacy).where(Pharmacy.tg_id == user_id)
            )
            pharmacy_admin = pharmacy_admin.scalar_one_or_none()

            if pharmacy_admin:
                await message.answer(
                    f"Salom, {username} 👋\n\nSiz dorixona admini sifatida tizimga kirdingiz!",
                    reply_markup=get_pharmacy_menu()
                )
            else:
                await message.answer(
                    f"Salom, {username} 👋\n\nSiz allaqachon ro'yxatdan o'tgansiz!",
                    reply_markup=get_main_menu()
                )


@router.message(F.contact, StateFilter(None))
async def save_user_contact(message: types.Message, state: FSMContext):
    """
    Save the user's phone number and other details to the database.
    Only handles contact when user is not in any FSM state.
    """
    async with async_session() as session:
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.full_name
        fullname = message.from_user.full_name
        phone_number = message.contact.phone_number

        # Check if user already exists
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            # User already exists, just update phone number if needed
            if existing_user.phone_number != phone_number:
                existing_user.phone_number = phone_number
                await session.commit()
            
            await message.answer(
                "Siz allaqachon ro'yxatdan o'tgansiz! Asosiy menyudan foydalaning.",
                reply_markup=get_main_menu()
            )
        else:
            # Create new user
            new_user = User(
                telegram_id=user_id,
                username=username,
                fullname=fullname,
                phone_number=phone_number,
                status=UserStatus.REGULAR.value
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


class SendMessageState(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_message = State()


@router.message(Command("send"))
async def send_message_command(message: types.Message, state: FSMContext):
    """
    Handle the /send command for the admin.
    Ask the admin for the user ID to whom the message should be sent.
    """
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        await message.answer("❌ Ushbu buyruq faqat admin uchun mavjud.")
        return

    await message.answer("📩 Iltimos, xabar yubormoqchi bo'lgan foydalanuvchining ID raqamini kiriting:")
    await state.set_state(SendMessageState.waiting_for_user_id)


@router.message(SendMessageState.waiting_for_user_id)
async def get_user_id(message: types.Message, state: FSMContext):
    """
    Save the user ID entered by the admin and ask for the message to send.
    """
    try:
        user_id = int(message.text)
        await state.update_data(user_id=user_id)
        await message.answer("✉️ Endi yubormoqchi bo'lgan xabaringizni kiriting:")
        await state.set_state(SendMessageState.waiting_for_message)
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri ID raqamini kiriting.")


@router.message(SendMessageState.waiting_for_message)
async def send_message_to_user(message: types.Message, state: FSMContext):
    """
    Send the message entered by the admin to the specified user.
    """
    data = await state.get_data()
    user_id = data.get("user_id")
    text = message.text

    try:
        await message.bot.send_message(user_id, text)
        await message.answer("✅ Xabar muvaffaqiyatli yuborildi!")
    except Exception as e:
        await message.answer(f"❌ Xabar yuborilmadi. Xatolik: {e}")

    await state.clear()

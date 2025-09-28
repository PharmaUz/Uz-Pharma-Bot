from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import async_session
from database.models import User  
from keyboards.main_menu import get_main_menu
from handlers.cooperation import ADMIN_ID

router = Router()


@router.message(Command("start"))
async def start_handler(message: types.Message):
    """
    Handle the /start command.
    Save user basic info and ask for contact if not exists.
    """
    telegram_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username

    async with async_session() as session:
        # check if user exists
        existing_user = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = existing_user.scalar_one_or_none()

        if not user:
            # create new user with no contact yet
            new_user = User(
                telegram_id=telegram_id,
                full_name=full_name,
                username=username,
                phone_number=None
            )
            session.add(new_user)
            await session.commit()

            # ask for contact
            contact_btn = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📱 Kontaktni yuborish", request_contact=True)]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            await message.answer(
                "Iltimos, telefon raqamingizni yuboring 📲",
                reply_markup=contact_btn
            )
        else:
            # user already exists, show menu
            await message.answer(
                f"Salom, {full_name or username} 👋",
                reply_markup=get_main_menu()
            )


@router.message(F.contact)
async def save_contact(message: types.Message):
    """
    Save user's phone number after they share contact.
    """
    telegram_id = message.from_user.id
    phone_number = message.contact.phone_number

    async with async_session() as session:
        existing_user = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = existing_user.scalar_one_or_none()

        if user:
            user.phone_number = phone_number
            await session.commit()

    await message.answer(
        "✅ Telefon raqamingiz saqlandi!\n\n🏠 Asosiy menyu:",
        reply_markup=get_main_menu()
    )
    
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

import html
import json
import math

from typing import Optional

from aiogram import Router, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.admin_menu import users_menu

from sqlalchemy.future import select

from database.models import User
from database.db import async_session
from sqlalchemy import func

router = Router()

USERS_PER_PAGE = 10  # Number of users to display per page

async def safe_edit_message_text(
    message: types.Message, 
    text: str, 
    reply_markup: Optional[types.InlineKeyboardMarkup] = None
) -> None:
    """
    Safely edit a message's text to avoid Telegram's "message is not modified" error.
    """
    try:
        # Compare text
        text_changed = message.text != text
        
        # Compare markup by converting to dict and then to JSON string
        current_markup_json = json.dumps(
            message.reply_markup.model_dump() if message.reply_markup else None,
            sort_keys=True
        )
        new_markup_json = json.dumps(
            reply_markup.model_dump() if reply_markup else None,
            sort_keys=True
        )
        markup_changed = current_markup_json != new_markup_json

        if text_changed or markup_changed:
            await message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        print(f"Error editing message: {e}")

@router.callback_query(lambda c: c.data and c.data.startswith("admin:users") and c.data != "admin:users:list")
async def handle_users_menu(callback: CallbackQuery):
    """
    Handle user management menu interactions.
    """
    await callback.answer()  # Answer the callback immediately
    await safe_edit_message_text(
        callback.message,
        "Foydalanuvchilarni boshqarish menyusi:",
        reply_markup=users_menu()
    )

@router.callback_query(lambda c: c.data and c.data.startswith("admin:users:list"))
async def list_users(callback: CallbackQuery):
    """
    Handle the "Ro'yxat" button to display a list of all users with pagination.
    """
    await callback.answer()  # Answer immediately to stop loading
    
    # Parse page number from callback data
    parts = callback.data.split(":")
    page = int(parts[3]) if len(parts) > 3 else 1
    
    async with async_session() as session:
        # Get total count
        # Get total count efficiently
        total_users = await session.scalar(select(func.count(User.id)))

        # Still fetch users (kept for existing pagination/slicing logic).
        # Ordering by id makes pagination deterministic.
        result = await session.execute(select(User).order_by(User.id))
        all_users = result.scalars().all()
    if total_users == 0:
        await safe_edit_message_text(
            callback.message, 
            "Foydalanuvchilar ro'yxati bo'sh.",
            reply_markup=users_menu()
        )
        return
    
    # Calculate pagination
    total_pages = math.ceil(total_users / USERS_PER_PAGE)
    page = max(1, min(page, total_pages))  # Ensure page is within valid range
    
    start_idx = (page - 1) * USERS_PER_PAGE
    end_idx = start_idx + USERS_PER_PAGE
    
    # Get users for current page
    users_page = all_users[start_idx:end_idx]
    
    # Format the user list
    user_list = "\n".join([
        f"{idx + start_idx + 1}. {html.escape(user.fullname or 'Nomalum')} "
        f"(@{html.escape(user.username or 'N/A')}) - "
        f"{html.escape(user.phone_number or 'Telefon raqam mavjud emas!')}"
        for idx, user in enumerate(users_page)
    ])
    
    # Create pagination keyboard
    keyboard = []
    nav_buttons = []
    
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"admin:users:list:{page-1}")
        )
    
    nav_buttons.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop")
    )
    
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"admin:users:list:{page+1}")
        )
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin:users")
    ])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    text = (
        f"<b>Foydalanuvchilar ro'yxati</b>\n"
        f"Jami: {total_users} ta foydalanuvchi\n\n"
        f"{user_list}"
    )
    
    await safe_edit_message_text(
        callback.message,
        text,
        reply_markup=reply_markup
    )

@router.callback_query(lambda c: c.data == "noop")
async def handle_noop(callback: CallbackQuery):
    """Handle no-operation callback (page indicator)"""
    await callback.answer()
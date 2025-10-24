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

@router.callback_query(lambda c: c.data and c.data.startswith("admin:users") and not c.data.startswith("admin:users:list"))
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
        # Get total count efficiently
        total_users = int(await session.scalar(select(func.count(User.id))) or 0)

        # Normalize page based on total_users so we fetch the correct slice
        total_pages = math.ceil(total_users / USERS_PER_PAGE) if total_users else 1
        page = max(1, min(page, total_pages))

        # Calculate offset for the current page and fetch only that page
        offset = (page - 1) * USERS_PER_PAGE
        result = await session.execute(
            select(User).order_by(User.id).limit(USERS_PER_PAGE).offset(offset)
        )
        page_users = result.scalars().all()

        # Provide an object that supports slicing as the original code expects
        class _PagedWindow:
            def __init__(self, items, offset, total):
                self._items = items
                self._offset = offset
                self._total = total

            def __getitem__(self, key):
                if isinstance(key, slice):
                    start = 0 if key.start is None else key.start
                    stop = self._total if key.stop is None else key.stop
                    rel_start = max(0, start - self._offset)
                    rel_stop = max(0, stop - self._offset)
                    return self._items[rel_start:rel_stop]
                else:
                    rel = key - self._offset
                    if 0 <= rel < len(self._items):
                        return self._items[rel]
                    raise IndexError

        # all_users behaves like the full list when sliced, but only fetches the current page
        all_users = _PagedWindow(page_users, offset, total_users)
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
        InlineKeyboardButton(text="🔙 Ortga", callback_data="admin:users")
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
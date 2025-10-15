from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_pharmacy_menu():
    """Dorixona egasi uchun inline menyu"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Buyurtmalar", callback_data="pharmacy_orders")],
        [InlineKeyboardButton(text="⏳ Kutilayotgan", callback_data="pharmacy_pending")],
        [InlineKeyboardButton(text="✅ Tasdiqlangan", callback_data="pharmacy_confirmed")],
        [InlineKeyboardButton(text="🔔 Tayyor", callback_data="pharmacy_ready")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="pharmacy_stats")],
    ])
    return keyboard

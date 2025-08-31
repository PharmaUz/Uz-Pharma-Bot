from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu():
    """Return the main menu inline keyboard"""
    menu_buttons = [
        [InlineKeyboardButton(text="💊 Dori qidirish", callback_data="search_drug")],
        [InlineKeyboardButton(text="🚚 Dori yetkazib berish", callback_data="delivery")],
        [InlineKeyboardButton(text="🤖 AI konsultatsiya", callback_data="ai_consult")],
        [InlineKeyboardButton(text="🤝 Hamkorlik", callback_data="cooperation")],
        [InlineKeyboardButton(text="💬 Fikr", callback_data="feedback")],
        [InlineKeyboardButton(text="📦 Mening buyurtmalarim", callback_data="my_orders")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=menu_buttons)


def get_confirm_keyboard():
    """Return confirmation keyboard with Yes/No buttons"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ha", callback_data="confirm_yes")],
            [InlineKeyboardButton(text="❌ Yo‘q", callback_data="confirm_no")],
        ]
    )

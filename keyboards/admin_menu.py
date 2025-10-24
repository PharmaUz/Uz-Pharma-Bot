from typing import List, Optional
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def admin_main_menu() -> InlineKeyboardMarkup:
    """
    Main admin menu
    """
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin:users"),
             InlineKeyboardButton(text="💊 Mahsulotlar", callback_data="admin:products")],
            [InlineKeyboardButton(text="🧾 Buyurtmalar", callback_data="admin:orders"),
             InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="admin:settings")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin:back")]
        ]
    )
    return kb


def users_menu() -> InlineKeyboardMarkup:
    """
    User management menu
    """
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Ro'yxat", callback_data="admin:users:list"),
             InlineKeyboardButton(text="🔎 Qidirish", callback_data="admin:users:search")],
            [InlineKeyboardButton(text="🚫 Ban qilish", callback_data="admin:users:ban"),
             InlineKeyboardButton(text="✅ Banni olib tashlash", callback_data="admin:users:unban")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin:back")]
        ]
    )
    return kb


def product_menu() -> InlineKeyboardMarkup:
    """
    Products management menu.
    """
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Qo'shish", callback_data="admin:products:add"),
             InlineKeyboardButton(text="✏️ Tahrirlash", callback_data="admin:products:edit")],
            [InlineKeyboardButton(text="🗑️ O'chirish", callback_data="admin:products:delete"),
             InlineKeyboardButton(text="📁 Katalog", callback_data="admin:products:catalog")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin:back")]
        ]
    )
    return kb


def confirm_keyboard(
    confirm_text: str = "✅ Tasdiqlash",
    cancel_text: str = "❌ Bekor qilish",
    confirm_data: str = "admin:confirm",
    cancel_data: str = "admin:cancel",
) -> InlineKeyboardMarkup:
    """
    Confirm/cancel buttons.
    """
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=confirm_text, callback_data=confirm_data),
             InlineKeyboardButton(text=cancel_text, callback_data=cancel_data)]
        ]
    )
    return kb


def simple_back_keyboard(callback_data: str = "admin:back", text: str = "⬅️ Ortga") -> InlineKeyboardMarkup:
    """
    Back button only.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=callback_data)]]
    )


def pagination_keyboard(
    page: int,
    prefix: str,
    has_prev: bool,
    has_next: bool,
    show_close: bool = True,
) -> InlineKeyboardMarkup:
    """
    Inline keyboard for pagination.
    prefix example: "admin:users:page" and callback_data format: "{prefix}:{page}".
    """
    buttons: List[List[InlineKeyboardButton]] = []

    # Pagination buttons
    row = []
    if has_prev:
        row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"{prefix}:{page-1}"))
    else:
        row.append(InlineKeyboardButton(text=" ", callback_data="admin:nop"))  # placeholder

    row.append(InlineKeyboardButton(text=f"• {page} •", callback_data="admin:nop_page"))

    if has_next:
        row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"{prefix}:{page+1}"))
    else:
        row.append(InlineKeyboardButton(text=" ", callback_data="admin:nop"))

    buttons.append(row)

    # Back and close buttons
    row2 = [InlineKeyboardButton(text="🔙 Ortga", callback_data="admin:back")]
    if show_close:
        row2.append(InlineKeyboardButton(text="❌ Yopish", callback_data="admin:close"))
    buttons.append(row2)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_item_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """
    Product-specific buttons (for example, on individual product page).
    """
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"admin:product:{product_id}:edit"),
             InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"admin:product:{product_id}:delete")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin:products")]
        ]
    )
    return kb


def orders_menu() -> InlineKeyboardMarkup:
    """
    Orders management menu.
    """
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Ro'yxat", callback_data="admin:orders:list"),
             InlineKeyboardButton(text="🔎 Qidirish", callback_data="admin:orders:search")],
            [InlineKeyboardButton(text="✅ Holatni yangilash", callback_data="admin:orders:update_status"),
             InlineKeyboardButton(text="🗑️ O'chirish", callback_data="admin:orders:delete")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin:back")]
        ]
    )
    return kb


def settings_menu() -> InlineKeyboardMarkup:
    """
    Settings menu.
    """
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Zaxira nusxasini yaratish", callback_data="admin:settings:backup"),
             InlineKeyboardButton(text="♻️ Ma'lumotlarni tiklash", callback_data="admin:settings:restore")],
            [InlineKeyboardButton(text="🛠️ Tizim sozlamalari", callback_data="admin:settings:system")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin:back")]
        ]
    )
    return kb
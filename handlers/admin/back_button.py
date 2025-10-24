from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import Router, types
from aiogram.types import CallbackQuery
from keyboards.admin_menu import admin_main_menu

router = Router()

@router.callback_query(lambda c: c.data == "admin:back")
async def handle_back_button(callback: CallbackQuery):
    """
    Handle the back button to return to the main admin menu.
    """
    await callback.message.edit_text(
        "Admin bosh menyusi:\nBu qisim keyingi versiyalar uchun, to'liq emas, kamchiliklar bor 📈",
        reply_markup=admin_main_menu()
    )

def simple_back_keyboard(callback_data: str = "admin:back", text: str = "⬅️ Ortga") -> InlineKeyboardMarkup:
    """
    Back button only
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=callback_data)]]
    )
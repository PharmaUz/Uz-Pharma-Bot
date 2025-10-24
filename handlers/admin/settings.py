from aiogram import Router, types
from aiogram.types import CallbackQuery
from keyboards.admin_menu import settings_menu

router = Router()

@router.callback_query(lambda c: c.data and c.data.startswith("admin:settings"))
async def handle_settings_menu(callback: CallbackQuery):
    """
    Handle admin settings menu interactions.
    """
    await callback.message.edit_text(
        "Sozlamalar menyusi:",
        reply_markup=settings_menu()
    )
from aiogram import Router, types
from aiogram.types import CallbackQuery
from keyboards.admin_menu import orders_menu

router = Router()

@router.callback_query(lambda c: c.data and c.data.startswith("admin:orders"))
async def handle_orders_menu(callback: CallbackQuery):
    """
    Handle order management menu interactions.
    """
    await callback.message.edit_text(
        "Buyurtmalarni boshqarish menyusi:",
        reply_markup=orders_menu()
    )
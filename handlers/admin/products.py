from aiogram import Router, types
from aiogram.types import CallbackQuery
from keyboards.admin_menu import product_menu

router = Router()

@router.callback_query(lambda c: c.data and c.data.startswith("admin:products"))
async def handle_products_menu(callback: CallbackQuery):
    """
    Handle product management menu interactions.
    """
    await callback.answer()
    await callback.message.edit_text(
        "Mahsulotlarni boshqarish menyusi:",
        reply_markup=product_menu()
    )
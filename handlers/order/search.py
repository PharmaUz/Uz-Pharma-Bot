import logging

from . import router

from loader import bot
from aiogram import types
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy import select, delete

from database.db import async_session
from database.models import Drug, Cart, Pharmacy, PharmacyDrug, Order, OrderItem

from keyboards.main_menu import get_main_menu

logger = logging.getLogger(__name__)


async def show_main_menu(message: types.Message, user: types.User):
    """
    Display main menu to user.
    """
    main_keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🛒 Savatni ko'rish",
                    callback_data="view_cart"
                ),
                types.InlineKeyboardButton(
                    text="🔍 Dori qidirish",
                    callback_data="buy_drug"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="📋 Buyurtmalarim",
                    callback_data="my_orders"
                ),
                types.InlineKeyboardButton(
                    text="ℹ️ Ma'lumot",
                    callback_data="info"
                )
            ]
        ]
    )

    await message.answer(
        f"👋 Assalomu alaykum, {user.first_name}!\n\n"
        "🏥 Dorixona botiga xush kelibsiz!\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=main_keyboard,
        parse_mode="HTML"
    )


@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    """
    Return to main menu.
    """
    await show_main_menu(callback.message, callback.from_user)
    


# =================== Drug Search =================== #
@router.callback_query(lambda c: c.data == "buy_drug")
async def start_drug_search(callback: types.CallbackQuery, state: FSMContext | None = None):
    """
    Start drug search process.
    """
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🔍 Dorilarni qidirish",
                    switch_inline_query_current_chat=""
                )
            ]
        ]
    )

    await callback.message.answer(
        "🏥 Dorilar sotuv bo'limi\n"
        "Pastdagi tugmani bosing va dori nomini yozing 👇",
        reply_markup=keyboard
    )
    await callback.answer()
    
    
    
    
# =================== Cart Functionality =================== #
@router.callback_query(lambda c: c.data.startswith("add_to_cart:"))
async def add_to_cart(callback: CallbackQuery):
    """
    Add drug to user's cart or increase quantity if already exists.
    """
    try:
        drug_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        async with async_session() as session:
            # Check if drug exists
            drug = await session.get(Drug, drug_id)
            if not drug:
                await callback.answer("❌ Dori topilmadi!", show_alert=True)
                return

            # Check if item already in cart
            existing_cart_item = await session.execute(
                select(Cart).where(
                    Cart.user_id == user_id,
                    Cart.drug_id == drug_id
                )
            )
            cart_item = existing_cart_item.scalar_one_or_none()

            if cart_item:
                # If exists, increase quantity
                cart_item.quantity += 1
                await session.commit()
                await callback.answer("✅ Dori miqdori oshirildi!", show_alert=True)
            else:
                # If not exists, create new cart item
                new_cart_item = Cart(
                    user_id=user_id,
                    drug_id=drug_id,
                    quantity=1
                )
                session.add(new_cart_item)
                await session.commit()
                await callback.answer("✅ Dori savatga qo'shildi!", show_alert=True)

        # Send main menu
        if callback.message:
            await callback.message.answer("🏠 Asosiy menyu:", reply_markup=get_main_menu())
        else:
            await bot.send_message(user_id, "🏠 Asosiy menyu:", reply_markup=get_main_menu())

    except ValueError:
        logger.error("Invalid drug_id format in callback data")
        await callback.answer("❌ Noto'g'ri ma'lumot formati", show_alert=True)
    except Exception as e:
        logger.error(f"Error adding to cart: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)

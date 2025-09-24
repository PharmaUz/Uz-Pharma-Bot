import math
import random
import string
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import selectinload

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from sqlalchemy import select

from database.db import async_session
from database.models import Drug, Cart

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(lambda c: c.data == "buy_drug")
async def start_drug_search(callback: types.CallbackQuery, state: FSMContext):
    """Start drug search"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text="🔍 Dorilarni qidirish",
                switch_inline_query_current_chat=""
            )]
        ]
    )

    await callback.message.answer(
        "🏥 Dorilar sotuv bo'limi\n"
        "Pastdagi tugmani bosing va dori nomini yozing 👇",
        reply_markup=keyboard
    )
    await callback.answer()


# Cart functionality handlers
@router.callback_query(lambda c: c.data.startswith("add_to_cart:"))
async def add_to_cart(callback: types.CallbackQuery):
    """Add drug to user's cart"""
    from database.models import Cart
    
    try:
        drug_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id
        
        async with async_session() as session:
            # Check if drug is already in cart
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
                # If doesn't exist, add new item
                new_cart_item = Cart(
                    user_id=user_id,
                    drug_id=drug_id,
                    quantity=1
                )
                session.add(new_cart_item)
                await session.commit()
                await callback.answer("✅ Dori savatga qo'shildi!", show_alert=True)
                
            # Show main menu after adding to cart
            await show_main_menu(callback.message, callback.from_user)
            
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


async def show_main_menu(message, user):
    """Show main menu to user"""
    main_keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🛒 Savatni ko'rish",
                    callback_data="view_cart"
                ),
                types.InlineKeyboardButton(
                    text="🔍 Dori qidirish",
                    callback_data="search_drug"
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


@router.callback_query(lambda c: c.data == "view_cart")
async def view_cart(callback: types.CallbackQuery):
    """Show user's cart"""
    from database.models import Cart, Drug
    
    try:
        user_id = callback.from_user.id
        
        async with async_session() as session:
            # Get cart items with drug information
            stmt = select(Cart, Drug).join(Drug).where(Cart.user_id == user_id)
            result = await session.execute(stmt)
            cart_items = result.all()
            
            if not cart_items:
                await callback.answer("🛒 Savat bo'sh!", show_alert=True)
                return
                
            # Build cart message
            cart_text = "🛒 <b>Sizning savatingiz:</b>\n\n"
            total_amount = 0
            
            cart_keyboard_buttons = []
            
            for i, (cart_item, drug) in enumerate(cart_items, 1):
                item_total = (drug.price or 0) * cart_item.quantity
                total_amount += item_total
                
                cart_text += (
                    f"{i}. <b>{drug.name}</b>\n"
                    f"   📦 Miqdor: {cart_item.quantity}\n"
                    f"   💰 Narxi: {drug.price or 0:,} so'm × {cart_item.quantity} = {item_total:,} so'm\n"
                    f"   ➖ ➕ ❌\n\n"
                )
                
                # Add quantity control buttons
                cart_keyboard_buttons.append([
                    types.InlineKeyboardButton(
                        text="➖",
                        callback_data=f"decrease_qty:{cart_item.id}"
                    ),
                    types.InlineKeyboardButton(
                        text=f"{cart_item.quantity}",
                        callback_data=f"item_info:{cart_item.id}"
                    ),
                    types.InlineKeyboardButton(
                        text="➕",
                        callback_data=f"increase_qty:{cart_item.id}"
                    ),
                    types.InlineKeyboardButton(
                        text="❌",
                        callback_data=f"remove_from_cart:{cart_item.id}"
                    )
                ])
            
            cart_text += f"💵 <b>Jami: {total_amount:,} so'm</b>"
            
            # Add control buttons
            cart_keyboard_buttons.extend([
                [
                    types.InlineKeyboardButton(
                        text="⬅️ Ortga",
                        callback_data="back_to_search"
                    ),
                    types.InlineKeyboardButton(
                        text="✅ Buyurtma berish",
                        callback_data="place_order"
                    )
                ]
            ])
            
            cart_keyboard = types.InlineKeyboardMarkup(inline_keyboard=cart_keyboard_buttons)
            
            await callback.message.edit_text(
                text=cart_text,
                parse_mode="HTML",
                reply_markup=cart_keyboard
            )
            
    except Exception as e:
        logger.error(f"Error viewing cart: {e}")
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(lambda c: c.data.startswith("increase_qty:"))
async def increase_quantity(callback: types.CallbackQuery):
    """Increase item quantity in cart"""
    from database.models import Cart
    
    try:
        cart_item_id = int(callback.data.split(":")[1])
        
        async with async_session() as session:
            cart_item = await session.get(Cart, cart_item_id)
            if cart_item and cart_item.user_id == callback.from_user.id:
                cart_item.quantity += 1
                await session.commit()
                await callback.answer("✅ Miqdor oshirildi!")
                # Refresh cart view
                await view_cart(callback)
            else:
                await callback.answer("❌ Xatolik yuz berdi")
                
    except Exception as e:
        logger.error(f"Error increasing quantity: {e}")
        await callback.answer("❌ Xatolik yuz berdi")


@router.callback_query(lambda c: c.data.startswith("decrease_qty:"))
async def decrease_quantity(callback: types.CallbackQuery):
    """Decrease item quantity in cart"""
    from database.models import Cart
    
    try:
        cart_item_id = int(callback.data.split(":")[1])
        
        async with async_session() as session:
            cart_item = await session.get(Cart, cart_item_id)
            if cart_item and cart_item.user_id == callback.from_user.id:
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    await session.commit()
                    await callback.answer("✅ Miqdor kamaytirildi!")
                else:
                    # Remove item if quantity becomes 0
                    await session.delete(cart_item)
                    await session.commit()
                    await callback.answer("✅ Mahsulot savatdan o'chirildi!")
                    
                # Refresh cart view
                await view_cart(callback)
            else:
                await callback.answer("❌ Xatolik yuz berdi")
                
    except Exception as e:
        logger.error(f"Error decreasing quantity: {e}")
        await callback.answer("❌ Xatolik yuz berdi")


@router.callback_query(lambda c: c.data.startswith("remove_from_cart:"))
async def remove_from_cart(callback: types.CallbackQuery):
    """Remove item from cart"""
    from database.models import Cart
    
    try:
        cart_item_id = int(callback.data.split(":")[1])
        
        async with async_session() as session:
            cart_item = await session.get(Cart, cart_item_id)
            if cart_item and cart_item.user_id == callback.from_user.id:
                await session.delete(cart_item)
                await session.commit()
                await callback.answer("✅ Mahsulot savatdan o'chirildi!", show_alert=True)
                
                # Check if cart is empty after deletion
                remaining_items = await session.execute(
                    select(Cart).where(Cart.user_id == callback.from_user.id)
                )
                if not remaining_items.scalars().all():
                    # If cart is empty, show main menu
                    await show_main_menu(callback.message, callback.from_user)
                else:
                    # Refresh cart view
                    await view_cart(callback)
            else:
                await callback.answer("❌ Xatolik yuz berdi")
                
    except Exception as e:
        logger.error(f"Error removing from cart: {e}")
        await callback.answer("❌ Xatolik yuz berdi")


@router.callback_query(lambda c: c.data == "back_to_search")
async def back_to_search(callback: types.CallbackQuery):
    """Go back to search"""
    await start_drug_search(callback, None)


@router.callback_query(lambda c: c.data == "place_order")
async def place_order(callback: types.CallbackQuery, state: FSMContext):
    """Start order placement process"""
    await callback.message.edit_text(
        "📋 <b>Buyurtma berish</b>\n\n"
        "Buyurtmani rasmiylashtirish uchun quyidagi ma'lumotlarni kiriting:\n"
        "1. To'liq ismingiz\n"
        "2. Telefon raqamingiz\n"
        "3. Yetkazib berish manzili\n\n"
        "Yoki administrator bilan bog'laning: @admin_username",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="⬅️ Savatga qaytish",
                        callback_data="view_cart"
                    ),
                    types.InlineKeyboardButton(
                        text="📞 Admin bilan bog'lanish",
                        url="https://t.me/admin_username"
                    )
                ]
            ]
        )
    )

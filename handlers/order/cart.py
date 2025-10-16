import logging

from . import router
from aiogram import types
from database.db import async_session
from database.models import Drug, Cart, Pharmacy, PharmacyDrug, Order, OrderItem
from sqlalchemy import select

logger = logging.getLogger(__name__)


@router.callback_query(lambda c: c.data.startswith("increase_qty:"))
async def increase_quantity(callback: types.CallbackQuery):
    """
    Increase quantity of item in cart.
    """
    try:
        cart_item_id = int(callback.data.split(":")[1])

        async with async_session() as session:
            cart_item = await session.get(Cart, cart_item_id)
            if cart_item and cart_item.user_id == callback.from_user.id:
                cart_item.quantity += 1
                await session.commit()
                await callback.answer("✅ Miqdor oshirildi!")
                await view_cart(callback)
            else:
                await callback.answer("❌ Xatolik yuz berdi", show_alert=True)

    except ValueError:
        logger.error("Invalid cart_item_id format")
        await callback.answer("❌ Noto'g'ri ma'lumot", show_alert=True)
    except Exception as e:
        logger.error(f"Error increasing quantity: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        
        

@router.callback_query(lambda c: c.data.startswith("decrease_qty:"))
async def decrease_quantity(callback: types.CallbackQuery):
    """
    Decrease quantity of item in cart or remove if quantity becomes 0.
    """
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
                    await session.delete(cart_item)
                    await session.commit()
                    await callback.answer("✅ Mahsulot savatdan o'chirildi!")

                await view_cart(callback)
            else:
                await callback.answer("❌ Xatolik yuz berdi", show_alert=True)

    except ValueError:
        logger.error("Invalid cart_item_id format")
        await callback.answer("❌ Noto'g'ri ma'lumot", show_alert=True)
    except Exception as e:
        logger.error(f"Error decreasing quantity: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(lambda c: c.data.startswith("remove_from_cart:"))
async def remove_from_cart(callback: types.CallbackQuery):
    """
    Remove item from cart completely.
    """
    try:
        cart_item_id = int(callback.data.split(":")[1])

        async with async_session() as session:
            cart_item = await session.get(Cart, cart_item_id)
            if cart_item and cart_item.user_id == callback.from_user.id:
                await session.delete(cart_item)
                await session.commit()
                await callback.answer(
                    "✅ Mahsulot savatdan o'chirildi!", show_alert=True
                )

                # Check if cart is empty
                remaining_items = await session.execute(
                    select(Cart).where(Cart.user_id == callback.from_user.id)
                )
                if not remaining_items.scalars().all():
                    await callback.message.edit_text(
                        "🛒 Savatingiz bo'sh.\n\nDori qidirish uchun tugmani bosing:",
                        reply_markup=types.InlineKeyboardMarkup(
                            inline_keyboard=[
                                [types.InlineKeyboardButton(
                                    text="🔍 Dori qidirish",
                                    callback_data="buy_drug"
                                )]
                            ]
                        )
                    )
                else:
                    await view_cart(callback)
            else:
                await callback.answer("❌ Xatolik yuz berdi", show_alert=True)

    except ValueError:
        logger.error("Invalid cart_item_id format")
        await callback.answer("❌ Noto'g'ri ma'lumot", show_alert=True)
    except Exception as e:
        logger.error(f"Error removing from cart: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)



@router.callback_query(lambda c: c.data == "view_cart")
async def view_cart(callback: types.CallbackQuery):
    """
    Display user's shopping cart with all items.
    """
    try:
        user_id = callback.from_user.id

        async with async_session() as session:
            stmt = select(Cart, Drug).join(Drug).where(Cart.user_id == user_id)
            result = await session.execute(stmt)
            cart_items = result.all()

            if not cart_items:
                await callback.answer("🛒 Savat bo'sh!", show_alert=True)
                return

            cart_text = "🛒 <b>Sizning savatingiz:</b>\n\n"
            total_amount = 0
            cart_keyboard_buttons = []

            for i, (cart_item, drug) in enumerate(cart_items, 1):
                item_total = (drug.price or 0) * cart_item.quantity
                total_amount += item_total

                cart_text += (
                    f"{i}. <b>{drug.name}</b>\n"
                    f"   📦 Miqdor: {cart_item.quantity}\n"
                    f"   💰 Narxi: {drug.price or 0:,} so'm × "
                    f"{cart_item.quantity} = {item_total:,} so'm\n\n"
                )

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

            cart_keyboard_buttons.extend([
                [
                    types.InlineKeyboardButton(
                        text="⬅️ Ortga",
                        callback_data="back_to_main"
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
        logger.error(f"Error viewing cart: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)

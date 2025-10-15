from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards import get_pharmacy_menu
from sqlalchemy import select, func
from database.models import Pharmacy, Order
from database.db import async_session

router = Router()


@router.callback_query(F.data == "pharmacy_orders")
async def show_all_orders(callback: types.CallbackQuery):
    """
    Display all recent orders belonging to the pharmacy owner.
    Shows up to 10 latest orders in descending order by creation date.
    """
    async with async_session() as session:
        user_id = callback.from_user.id
        result = await session.execute(
            select(Pharmacy).where(Pharmacy.tg_id == user_id)
        )
        pharmacy = result.scalar_one_or_none()

        # If the user is not a pharmacy owner
        if not pharmacy:
            await callback.answer("Siz dorixona egasi emassiz!", show_alert=True)
            return

        # Retrieve the last 10 orders for the pharmacy
        result = await session.execute(
            select(Order)
            .where(Order.pharmacy_id == pharmacy.id)
            .order_by(Order.created_at.desc())
            .limit(10)
        )
        orders = result.scalars().all()

        # If there are no orders
        if not orders:
            await callback.message.edit_text(
                "Hozircha buyurtmalar yo‘q.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_pharmacy_menu")]
                    ]
                ),
            )
            return

        # Build message text
        text = f"📋 <b>{pharmacy.name}</b> - Buyurtmalar\n\n"

        for order in orders:
            # Emoji for order status
            status_emoji = {
                "pending": "⏳",
                "confirmed": "✅",
                "ready": "🔔",
                "completed": "✔️",
                "cancelled": "❌",
            }.get(order.status, "❓")

            # Add order details to message text
            text += (
                f"{status_emoji} <b>Buyurtma #{order.id}</b>\n"
                f"👤 {order.full_name}\n"
                f"📞 {order.phone}\n"
                f"💰 {order.total_amount:,} so‘m\n"
                f"📍 {order.delivery_type}\n"
                f"📊 Status: {order.status}\n"
                f"{'🔑 Kod: ' + order.pickup_code if order.pickup_code else ''}\n"
                f"━━━━━━━━━━━━━━━\n\n"
            )

        # Back button
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_pharmacy_menu")]
            ]
        )

        # Send message with orders
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.in_(["pharmacy_pending", "pharmacy_confirmed", "pharmacy_ready"]))
async def show_orders_by_status(callback: types.CallbackQuery):
    """
    Display pharmacy orders filtered by their current status.
    """
    async with async_session() as session:
        user_id = callback.from_user.id
        status_map = {
            "pharmacy_pending": "pending",
            "pharmacy_confirmed": "confirmed",
            "pharmacy_ready": "ready",
        }
        status = status_map[callback.data]

        # Get pharmacy by Telegram user ID
        result = await session.execute(
            select(Pharmacy).where(Pharmacy.tg_id == user_id)
        )
        pharmacy = result.scalar_one_or_none()

        # If user is not a pharmacy owner
        if not pharmacy:
            await callback.answer("Siz dorixona egasi emassiz!", show_alert=True)
            return

        # Get orders by selected status
        result = await session.execute(
            select(Order)
            .where(Order.pharmacy_id == pharmacy.id, Order.status == status)
            .order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()

        # Status title mapping
        status_titles = {
            "pending": "⏳ Kutilayotgan",
            "confirmed": "✅ Tasdiqlangan",
            "ready": "🔔 Tayyor",
        }

        # If there are no orders for this status
        if not orders:
            await callback.message.edit_text(
                f"{status_titles[status]} buyurtmalar yo‘q.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_pharmacy_menu")]
                    ]
                ),
            )
            return

        # Build message text
        text = f"<b>{status_titles[status]} buyurtmalar</b>\n\n"

        for order in orders:
            # Add order details
            text += (
                f"<b>Buyurtma #{order.id}</b>\n"
                f"👤 {order.full_name}\n"
                f"📞 {order.phone}\n"
                f"💰 {order.total_amount:,} so‘m\n"
                f"📍 {order.delivery_type}\n"
                f"{'🔑 Kod: ' + order.pickup_code if order.pickup_code else ''}\n"
                f"━━━━━━━━━━━━━━━\n\n"
            )

        # Back button
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_pharmacy_menu")]
            ]
        )

        # Send result message
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "pharmacy_stats")
async def show_pharmacy_stats(callback: types.CallbackQuery):
    """
    Display summarized statistics for the pharmacy:
    total orders, status breakdown, and total revenue.
    """
    async with async_session() as session:
        user_id = callback.from_user.id
        result = await session.execute(
            select(Pharmacy).where(Pharmacy.tg_id == user_id)
        )
        pharmacy = result.scalar_one_or_none()

        # If not a pharmacy owner
        if not pharmacy:
            await callback.answer("Siz dorixona egasi emassiz!", show_alert=True)
            return

        # Query statistics for this pharmacy
        result = await session.execute(
            select(
                func.count(Order.id).label("total"),
                func.count(Order.id).filter(Order.status == "pending").label("pending"),
                func.count(Order.id).filter(Order.status == "confirmed").label("confirmed"),
                func.count(Order.id).filter(Order.status == "ready").label("ready"),
                func.count(Order.id).filter(Order.status == "completed").label("completed"),
                func.sum(Order.total_amount).filter(Order.status == "completed").label("total_revenue"),
            ).where(Order.pharmacy_id == pharmacy.id)
        )
        stats = result.one()

        # Build message text with statistics
        text = (
            f"📊 <b>{pharmacy.name}</b> - Statistika\n\n"
            f"📦 Jami buyurtmalar: {stats.total}\n"
            f"⏳ Kutilayotgan: {stats.pending or 0}\n"
            f"✅ Tasdiqlangan: {stats.confirmed or 0}\n"
            f"🔔 Tayyor: {stats.ready or 0}\n"
            f"✔️ Yakunlangan: {stats.completed or 0}\n\n"
            f"💰 Jami daromad: {stats.total_revenue or 0:,} so‘m"
        )

        # Back button
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_pharmacy_menu")]
            ]
        )

        # Send statistics message
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "back_to_pharmacy_menu")
async def back_to_menu(callback: types.CallbackQuery):
    """
    Return to the pharmacy management main menu.
    """
    async with async_session() as session:
        user_id = callback.from_user.id
        result = await session.execute(
            select(Pharmacy).where(Pharmacy.tg_id == user_id)
        )
        pharmacy = result.scalar_one_or_none()

        # Show pharmacy info and control buttons
        if pharmacy:
            await callback.message.edit_text(
                f"<b>{pharmacy.name}</b> dorixonasi\n\n"
                f"Manzil: {pharmacy.address or 'Ko‘rsatilmagan'}\n\n"
                f"Quyidagi tugmalar orqali buyurtmalarni boshqaring:",
                reply_markup=get_pharmacy_menu(),
                parse_mode="HTML",
            )
        else:
            await callback.answer("Xatolik yuz berdi!", show_alert=True)

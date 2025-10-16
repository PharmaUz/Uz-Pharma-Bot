import random
import logging

from .import router
from loader import bot
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy import select, delete

from database.db import async_session
from database.models import Drug, Cart, Pharmacy, PharmacyDrug, Order, OrderItem

from keyboards.main_menu import get_main_menu
from .utils import calculate_distance

logger = logging.getLogger(__name__)


class OrderState(StatesGroup):
    """
    FSM states for order placement process.
    """
    choosing_delivery_type = State()
    waiting_for_location = State()
    choosing_pharmacy = State()
    confirming_order = State()



@router.callback_query(lambda c: c.data == "place_order")
async def place_order(callback: types.CallbackQuery, state: FSMContext):
    """
    Start order placement process - choose delivery type.
    """
    # Check if cart is not empty
    async with async_session() as session:
        cart_check = await session.execute(
            select(Cart).where(Cart.user_id == callback.from_user.id)
        )
        if not cart_check.scalars().all():
            await callback.answer("🛒 Savatingiz bo'sh!", show_alert=True)
            return

    await state.set_state(OrderState.choosing_delivery_type)

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🚶 Pickup (o'zi borib olish)",
                    callback_data="delivery_type:pickup"
                ),
                types.InlineKeyboardButton(
                    text="🚚 Yetkazib berish (Yandex)",
                    callback_data="delivery_type:delivery"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="⬅️ Savatga qaytish",
                    callback_data="view_cart"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "📦 <b>Buyurtmani qanday rasmiylashtirmoqchisiz?</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(
    OrderState.choosing_delivery_type,
    lambda c: c.data.startswith("delivery_type:")
)
async def handle_delivery_type(callback: types.CallbackQuery, state: FSMContext):
    """
    Handle delivery type selection.
    """
    delivery_type = callback.data.split(":")[1]

    if delivery_type == "delivery":
        await callback.answer(
            "🚚 Uzr, hozircha bu xizmatimiz vaqtincha ishlamayapti. Iltimos, Pickup ni tanlang.",
            show_alert=True
        )
        # Keep user in same state to allow reselection
        return

    elif delivery_type == "pickup":
        await state.update_data(delivery_type="pickup")
        await state.set_state(OrderState.waiting_for_location)

        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(
                        text="📍 Mening joylashuvim",
                        request_location=True
                    )
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await callback.message.answer(
            "<b>📍 Iltimos, joylashuvingizni yuboring</b>\n\n"
            "Sizning manzilingiz yordamida biz savatingizdagi dorilarni qamrab oladigan "
            "eng yaqin dorixonalarni topamiz.\n\n"
            "<b>Joylashuvni yuborish usullari:</b>\n"
            "• Tugmani bosing: <i>📍 Mening joylashuvim</i> (eng oson va tez usul).\n"
            "• Yoki Telegram orqali <i>Location</i> turidagi xabar yuboring.\n\n"
            "<b>Qanday ishlaydi:</b>\n"
            "1) Siz joylashuv yuborasiz, \n2) Biz savatingizni tekshiramiz, \n"
            "3) Sizga eng yaqin va kerakli dorilar mavjud dorixonalarni ko'rsatamiz.\n\n"
            "<i>Maxfiylik:</i> Joylashuvingiz faqat dorixona tanlash jarayonida ishlatiladi va saqlanmaydi.",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await callback.answer()




@router.message(OrderState.waiting_for_location)
async def handle_location(message: types.Message, state: FSMContext):
    """
    Handle user location and find nearby pharmacies with required drugs.
    """
    user_location = message.location
    if not user_location:
        await message.answer(
            "❌ Iltimos, joylashuvni pastdagi tugma orqali yuboring yoki "
            "Location turidagi xabar yuboring."
        )
        return

    user_lat, user_lon = user_location.latitude, user_location.longitude
    user_id = message.from_user.id

    # Remove location keyboard
    await message.answer(
        "🔎 Eng yaqin dorixonalarni qidirmoqdamiz...",
        reply_markup=types.ReplyKeyboardRemove()
    )

    try:
        async with async_session() as session:
            # Get user's cart items
            stmt_cart = select(Cart).where(Cart.user_id == user_id)
            cart_items_res = await session.execute(stmt_cart)
            cart_items = cart_items_res.scalars().all()

            if not cart_items:
                await message.answer(
                    "❌ Sizning savatingiz bo'sh. Qayta boshlash uchun /start bosing."
                )
                await state.clear()
                return

            required_drug_ids = {item.drug_id for item in cart_items}

            # Fetch all active pharmacies
            pharmacies_result = await session.execute(
                select(Pharmacy).where(Pharmacy.is_active == True)
            )
            all_pharmacies = pharmacies_result.scalars().all()

            if not all_pharmacies:
                await message.answer(
                    "❌ Uzr, tizimda hech qanday dorixona topilmadi. "
                    "Iltimos, keyinroq urinib ko'ring."
                )
                await state.clear()
                return

            eligible_pharmacies = []

            # Check each pharmacy for drug availability
            for pharmacy in all_pharmacies:
                pharmacy_drugs_result = await session.execute(
                    select(PharmacyDrug).where(
                        PharmacyDrug.pharmacy_id == pharmacy.id,
                        PharmacyDrug.drug_id.in_(required_drug_ids),
                        PharmacyDrug.residual > 0
                    )
                )
                available_drugs = pharmacy_drugs_result.scalars().all()
                available_drug_ids = {pd.drug_id for pd in available_drugs}

                if required_drug_ids.issubset(available_drug_ids):
                    # Foydalaniladigan koordinatalar modeldan olinadi
                    if pharmacy.latitude and pharmacy.longitude:
                        pharmacy_lat = float(pharmacy.latitude)
                        pharmacy_lon = float(pharmacy.longitude)
                    else:
                        # fallback agar bazada yo‘q bo‘lsa
                        pharmacy_lat = 41.2995  
                        pharmacy_lon = 69.2401  

                    distance = calculate_distance(user_lat, user_lon, pharmacy_lat, pharmacy_lon)

                    eligible_pharmacies.append({
                        "id": pharmacy.id,
                        "name": pharmacy.name,
                        "address": pharmacy.address or "Manzil ko'rsatilmagan",
                        "phone": pharmacy.phone or "",
                        "distance": distance,
                        "latitude": pharmacy.latitude,
                        "longitude": pharmacy.longitude,
                        "status": "Dorilar mavjud ✅"
                    })

            # Sort by distance and take top 3
            eligible_pharmacies.sort(key=lambda x: x["distance"])
            top_pharmacies = eligible_pharmacies[:3]

            if not top_pharmacies:
                await message.answer(
                    "❌ Uzr, savatingizdagi barcha dorilar mavjud bo'lgan "
                    "yaqin dorixona topilmadi.\n\n"
                    "Iltimos, savatni ko'rib chiqing va ayrim mahsulotlarni o'chirib, "
                    "qaytadan urinib ko'ring.",
                    reply_markup=types.InlineKeyboardMarkup(
                        inline_keyboard=[
                            [types.InlineKeyboardButton(
                                text="🛒 Savatni ko'rish",
                                callback_data="view_cart"
                            )]
                        ]
                    )
                )
                await state.clear()
                return

            # Display pharmacy options
            pharmacy_text = "<b>🏪 Sizga eng yaqin dorixonalar ro'yxati:</b>\n\n"
            keyboard_buttons = []

            for i, p in enumerate(top_pharmacies, 1):
                pharmacy_text += (
                    f"{i}. <b>{p['name']}</b>\n"
                    f"   📍 <a href='https://www.google.com/maps/search/?api=1&query={p['latitude']},{p['longitude']}'>{p['address']}</a>\n"
                    f"   📏 <i>{p['distance']:.2f} km</i> – {p['status']}\n"
                )
                if p['phone']:
                    pharmacy_text += f"   📞 {p['phone']}\n"
                pharmacy_text += "\n"

                keyboard_buttons.append([
                    types.InlineKeyboardButton(
                        text=f"{i}. {p['name']} ({p['distance']:.1f} km)",
                        callback_data=f"select_pharmacy:{p['id']}"
                    )
                ])

            keyboard_buttons.append([
                types.InlineKeyboardButton(
                    text="⬅️ Ortga (Qayta qidirish)",
                    callback_data="place_order"
                )
            ])

            await state.set_state(OrderState.choosing_pharmacy)
            await state.update_data(pharmacies=top_pharmacies)

            await message.answer(
                pharmacy_text,
                parse_mode="HTML",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            )

    except Exception as e:
        logger.error(f"Error handling location and searching pharmacies: {e}", exc_info=True)
        await message.answer(
            "❌ Dorixonalarni qidirishda kutilmagan xatolik yuz berdi.\n"
            "Iltimos, qaytadan urinib ko'ring."
        )
        await state.clear()


@router.callback_query(
    OrderState.choosing_pharmacy,
    lambda c: c.data.startswith("select_pharmacy:")
)
async def finalize_order_confirmation(callback: types.CallbackQuery, state: FSMContext):
    """
    Show order confirmation with selected pharmacy details.
    """
    try:
        pharmacy_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        data = await state.get_data()
        pharmacy_list = data.get("pharmacies", [])
        selected_pharmacy = next((p for p in pharmacy_list if p['id'] == pharmacy_id), None)

        if not selected_pharmacy:
            await callback.answer("❌ Tanlangan dorixona topilmadi.", show_alert=True)
            return

        total_amount = 0
        cart_items_details = []

        async with async_session() as session:
            stmt = select(Cart, Drug).join(Drug).where(Cart.user_id == user_id)
            result = await session.execute(stmt)
            cart_items = result.all()

            if not cart_items:
                await callback.answer("🛒 Savatingiz bo'sh!", show_alert=True)
                await state.clear()
                return

            cart_summary_text = ""
            for i, (cart_item, drug) in enumerate(cart_items, 1):
                item_total = (drug.price or 0) * cart_item.quantity
                total_amount += item_total

                cart_summary_text += (
                    f"{i}. <b>{drug.name}</b>: {cart_item.quantity} × "
                    f"{drug.price or 0:,} so'm = {item_total:,} so'm\n"
                )
                cart_items_details.append({
                    "drug_id": drug.id,
                    "drug_name": drug.name,
                    "quantity": cart_item.quantity,
                    "price": drug.price or 0
                })

        # Generate unique pickup code
        pickup_code = f"PX-{random.randint(10000, 99999)}"

        confirmation_text = (
            "<b>✅ Buyurtmani tasdiqlash</b>\n\n"
            "<b>🏪 Tanlangan dorixona (Pickup):</b>\n"
            f" 📍 {selected_pharmacy['name']}\n"
            f" 🏠 Manzil: <a href='https://www.google.com/maps/search/?api=1&query={selected_pharmacy['latitude']},{selected_pharmacy['longitude']}'>{selected_pharmacy['address']}</a>\n"
        )
        
        if selected_pharmacy.get('phone'):
            confirmation_text += f" 📞 Telefon: {selected_pharmacy['phone']}\n"
        
        confirmation_text += (
            f" 📏 Masofa: {selected_pharmacy['distance']:.2f} km\n\n"
            "<b>🛍 Buyurtma tafsilotlari:</b>\n"
            f"{cart_summary_text}\n"
            f"<b>💵 Jami to'lov: {total_amount:,} so'm</b>\n\n"
            "<b>⏰ Kutish vaqti:</b> Buyurtma 40 daqiqa ichida tayyor bo'ladi.\n\n"
            "<i>Iltimos, buyurtmani tasdiqlang. Tasdiqlangandan keyin "
            "sizga maxsus kod beriladi.</i>"
        )

        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="✅ Tasdiqlash va kod olish",
                        callback_data=f"confirm_pickup:{pharmacy_id}"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="⬅️ Dorixonani o'zgartirish",
                        callback_data="change_pharmacy"
                    )
                ]
            ]
        )

        await state.set_state(OrderState.confirming_order)
        await state.update_data(
            final_pharmacy_id=pharmacy_id,
            final_pharmacy_name=selected_pharmacy['name'],
            final_pharmacy_address=selected_pharmacy['address'],
            final_pharmacy_phone=selected_pharmacy.get('phone', ''),
            final_pharmacy_latitude=selected_pharmacy['latitude'],
            final_pharmacy_longitude=selected_pharmacy['longitude'],
            order_total=total_amount,
            order_items=cart_items_details,
            pickup_code=pickup_code
        )

        await callback.message.edit_text(
            confirmation_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await callback.answer()

    except ValueError:
        logger.error("Invalid pharmacy_id format")
        await callback.answer("❌ Noto'g'ri ma'lumot", show_alert=True)
    except Exception as e:
        logger.error(f"Error in order confirmation: {e}", exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(
    OrderState.confirming_order,
    lambda c: c.data == "change_pharmacy"
)
async def change_pharmacy(callback: types.CallbackQuery, state: FSMContext):
    """
    Allow user to go back and change pharmacy selection.
    """
    data = await state.get_data()
    pharmacy_list = data.get("pharmacies", [])

    if not pharmacy_list:
        await callback.answer("❌ Dorixonalar ro'yxati topilmadi", show_alert=True)
        return

    pharmacy_text = "<b>🏪 Sizga eng yaqin dorixonalar ro'yxati:</b>\n\n"
    keyboard_buttons = []

    for i, p in enumerate(pharmacy_list, 1):
        pharmacy_text += (
            f"{i}. <b>{p['name']}</b>\n"
            f"   📍 {p['address']}\n"
            f"   📏 <i>{p['distance']:.2f} km</i> – {p['status']}\n\n"
        )

        keyboard_buttons.append([
            types.InlineKeyboardButton(
                text=f"{i}. {p['name']} ({p['distance']:.1f} km)",
                callback_data=f"select_pharmacy:{p['id']}"
            )
        ])

    keyboard_buttons.append([
        types.InlineKeyboardButton(
            text="⬅️ Ortga",
            callback_data="place_order"
        )
    ])

    await state.set_state(OrderState.choosing_pharmacy)

    await callback.message.edit_text(
        pharmacy_text,
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    )
    await callback.answer()


@router.callback_query(
    OrderState.confirming_order,
    lambda c: c.data.startswith("confirm_pickup:")
)
async def finalize_order(callback: types.CallbackQuery, state: FSMContext):
    """
    Finalize order, save to database, clear cart, and send confirmation.
    """
    data = await state.get_data()
    pharmacy_id = data.get("final_pharmacy_id")
    pharmacy_name = data.get("final_pharmacy_name", "")
    pharmacy_address = data.get("final_pharmacy_address", "")
    pharmacy_phone = data.get("final_pharmacy_phone", "")
    pharmacy_latitude = data.get("final_pharmacy_latitude", 0)
    pharmacy_longitude = data.get("final_pharmacy_longitude", 0)
    total_amount = data.get("order_total", 0)
    order_items = data.get("order_items", [])
    pickup_code = data.get("pickup_code")
    user_id = callback.from_user.id

    if not pharmacy_id or not order_items:
        await callback.answer("❌ Buyurtma ma'lumotlari topilmadi", show_alert=True)
        await state.clear()
        return

    try:
        async with async_session() as session:
            # Create new order
            new_order = Order(
                user_id=user_id,
                full_name=callback.from_user.full_name or "Unknown",
                phone=pickup_code,  # Using pickup code as temporary identifier
                pharmacy_id=pharmacy_id,
                address=f"{pharmacy_name}, {pharmacy_address}",
                total_amount=total_amount,
                status="pending"
            )
            session.add(new_order)
            await session.flush()  # Get order ID

            # Create order items
            for item in order_items:
                order_item = OrderItem(
                    order_id=new_order.id,
                    drug_id=item['drug_id'],
                    quantity=item['quantity'],
                    price=item['price']
                )
                session.add(order_item)

            # Update pharmacy drug stock (reduce residual)
            for item in order_items:
                pharmacy_drug_result = await session.execute(
                    select(PharmacyDrug).where(
                        PharmacyDrug.pharmacy_id == pharmacy_id,
                        PharmacyDrug.drug_id == item['drug_id']
                    )
                )
                pharmacy_drug = pharmacy_drug_result.scalar_one_or_none()
                
                if pharmacy_drug and pharmacy_drug.residual >= item['quantity']:
                    pharmacy_drug.residual -= item['quantity']
                else:
                    logger.warning(
                        f"Insufficient stock for drug {item['drug_id']} "
                        f"at pharmacy {pharmacy_id}"
                    )

            # Clear user's cart
            await session.execute(
                delete(Cart).where(Cart.user_id == user_id)
            )
            
            await session.commit()

            # Send success message with pickup code
            final_message = (
                "🎉 <b>BUYURTMA MUVAFFAQIYATLI RASMIYLASHTIRILDI!</b>\n\n"
                f"📋 <b>Buyurtma raqami:</b> #{new_order.id}\n"
                f"🔐 <b>Pickup kod:</b> <code>{pickup_code}</code>\n\n"
                f"🏪 <b>Dorixona:</b> {pharmacy_name}\n"
                f"📞 <b>Telefon:</b> {pharmacy_phone}\n"
                f"📍 <b>Manzil:</b> <a href='https://www.google.com/maps/search/?api=1&query={pharmacy_latitude},{pharmacy_longitude}'>{pharmacy_address}</a>\n\n"
                f"💵 <b>To'lov summasi:</b> {total_amount:,} so'm\n\n"
                "⏰ <b>Olib ketish vaqti:</b> Hozirdan boshlab 40 daqiqa ichida.\n\n"
                "<b>⚠️ Muhim eslatmalar:</b>\n"
                "• Dorixonaga borganda pickup kodingizni ko'rsating\n"
                "• To'lov dorixonada amalga oshiriladi\n"
                "• Kod faqat bir marta ishlatiladi\n\n"
                "<i>Buyurtmalar tarixini ko'rish uchun \"📋 Buyurtmalarim\" bo'limiga o'ting.</i>"
            )

            await callback.message.edit_text(
                final_message,
                parse_mode="HTML",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="🏠 Asosiy menyu",
                                callback_data="back_to_main"
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="📋 Buyurtmalarim",
                                callback_data="my_orders"
                            )
                        ]
                    ]
                )
            )
            
            await callback.answer("✅ Buyurtma tasdiqlandi!", show_alert=True)
            await state.clear()

            logger.info(
                f"Order #{new_order.id} created successfully for user {user_id} "
                f"at pharmacy {pharmacy_id}"
            )
            # --- SEND MESSAGE TO PHARMACY ADMIN ---
            pharmacy = await session.get(Pharmacy, pharmacy_id)
            admin_tg_id = pharmacy.tg_id if pharmacy else None

            if admin_tg_id:
                order_items_text = ""
                for item in order_items:
                    order_items_text += (
                        f"- {item['drug_name']}: {item['quantity']} dona, {item['price']:,} so'm\n"
                    )
                admin_message = (
                    f"🆕 <b>Yangi buyurtma!</b>\n"
                    f"📋 Buyurtma raqami: #{new_order.id}\n"
                    f"👤 Mijoz: {callback.from_user.full_name or 'Unknown'}\n"
                    f"🔐 Pickup kod: <code>{pickup_code}</code>\n"
                    f"💵 Jami: {total_amount:,} so'm\n"
                    f"🛍 Buyurtma:\n{order_items_text}\n"
                    f"🏪 Dorixona: {pharmacy_name}\n"
                    f"📍 Manzil: {pharmacy_address}\n"
                    f"⏰ Olib ketish: 40 daqiqa ichida\n"
                )
                try:
                    await bot.send_message(
                        admin_tg_id,
                        admin_message,
                        parse_mode="HTML"
                    )
                except TelegramAPIError as err:
                    logger.error(f"Failed to send order notification to admin: {err}")

    except Exception as e:
        logger.error(f"Error finalizing order: {e}", exc_info=True)
        await callback.answer(
            "❌ Buyurtmani yakunlashda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
            show_alert=True
        )
        # Don't clear state so user can retry

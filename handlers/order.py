import logging
import math
import random

from loader import bot
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from sqlalchemy import select, delete

from database.db import async_session
from database.models import Drug, Cart, Pharmacy, PharmacyDrug, Order, OrderItem

from keyboards.main_menu import get_main_menu

router = Router()
logger = logging.getLogger(__name__)


class OrderState(StatesGroup):
    """
    FSM states for order placement process.
    """
    choosing_delivery_type = State()
    waiting_for_location = State()
    choosing_pharmacy = State()
    confirming_order = State()


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


@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    """
    Return to main menu.
    """
    await show_main_menu(callback.message, callback.from_user)


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
            "1) Siz joylashuv yuborasiz → 2) Biz savatingizni tekshiramiz \n"
            "3) Sizga eng yaqin va kerakli dorilar mavjud dorixonalarni ko'rsatamiz.\n\n"
            "<i>Maxfiylik:</i> Joylashuvingiz faqat dorixona tanlash jarayonida ishlatiladi va saqlanmaydi.",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await callback.answer()


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
    
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth radius in kilometers
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dLon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance


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
                    f"   📍 {p['address']}\n"
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
            f" 🏠 Manzil: {selected_pharmacy['address']}\n"
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
                f"📍 <b>Manzil:</b> {pharmacy_address}\n\n"
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

    except Exception as e:
        logger.error(f"Error finalizing order: {e}", exc_info=True)
        await callback.answer(
            "❌ Buyurtmani yakunlashda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
            show_alert=True
        )
        # Don't clear state so user can retry

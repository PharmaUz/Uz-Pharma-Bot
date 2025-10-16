import re
import os
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from keyboards.main_menu import get_confirm_keyboard, get_main_menu
from database.db import async_session
from database.models import Application
from dotenv import load_dotenv


# === Load environment variables ===
load_dotenv()
ADMIN_ID = os.getenv("ADMIN_ID")
if ADMIN_ID is None:
    raise ValueError("ADMIN_ID not found in .env file!")
ADMIN_ID = int(ADMIN_ID)

router = Router()


class CooperationForm(StatesGroup):
    """
    FSM for cooperation (partner application) process.
    Steps:
    - name → organization name
    - contact → contact info (phone/email)
    - address → address
    - license_photo → license/certificate photo
    - confirm → user confirmation
    """
    name = State()
    contact = State()
    address = State()
    license_photo = State()
    confirm = State()


@router.callback_query(lambda c: c.data == "cooperation")
async def start_cooperation(callback: types.CallbackQuery, state: FSMContext):
    """
    Step 1: Start cooperation process.
    Asks the user to enter organization name.
    """
    await callback.message.answer(
        "🤝 Hamkorlik moduli\n\n"
        "🏢 Tashkilot nomini kiriting:"
    )
    await state.set_state(CooperationForm.name)


@router.message(StateFilter(CooperationForm.name))
async def process_name(message: types.Message, state: FSMContext):
    """
    Step 2: Save organization name and ask for contact info.
    """
    await state.update_data(name=message.text)
    contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Kontaktni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "📞 Telefon raqamingizni kontakt sifatida yuboring:",
        reply_markup=contact_keyboard
    )
    await state.set_state(CooperationForm.contact)

@router.message(StateFilter(CooperationForm.contact))
async def process_contact(message: types.Message, state: FSMContext):
    """
    Step 3: Save contact info and ask for address.
    Faqat kontakt orqali yuborilgan telefon raqami qabul qilinadi.
    """
    if not message.contact or not message.contact.phone_number:
        await message.answer(
            "❌ Iltimos, 'Kontaktni yuborish' tugmasidan foydalaning."
        )
        return

    phone = message.contact.phone_number

    await state.update_data(contact=phone)
    await message.answer("📍 Manzilni kiriting:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(CooperationForm.address)


@router.message(StateFilter(CooperationForm.address))
async def process_address(message: types.Message, state: FSMContext):
    """
    Step 4: Save address and ask for license/certificate photo.
    """
    await state.update_data(address=message.text)
    await message.answer("📷 Litsenziya yoki sertifikat rasmini yuboring (foto):")
    await state.set_state(CooperationForm.license_photo)


@router.message(StateFilter(CooperationForm.license_photo))
async def process_license(message: types.Message, state: FSMContext):
    """
    Step 5: Save license photo and show confirmation message with summary.
    """
    if not message.photo:
        await message.answer("❌ Iltimos, rasm yuboring.")
        return

    photo_id = message.photo[-1].file_id
    await state.update_data(license_photo=photo_id)

    data = await state.get_data()
    caption = (
        "📋 Kiritilgan maʼlumotlar:\n\n"
        f"🏢 Tashkilot nomi: {data['name']}\n"
        f"📞 Aloqa: {data['contact']}\n"
        f"📍 Manzil: {data['address']}\n\n"
        "Maʼlumotlar to'g'rimi?"
    )

    await message.answer_photo(
        photo=photo_id,
        caption=caption,
        reply_markup=get_confirm_keyboard()
    )
    await state.set_state(CooperationForm.confirm)


@router.callback_query(StateFilter(CooperationForm.confirm))
async def confirm_data(callback: types.CallbackQuery, state: FSMContext):
    """
    Step 6: Handle user confirmation.
    - If yes → send application to admin
    - If no → cancel and return to main menu
    """
    data = await state.get_data()

    if callback.data == "confirm_yes":
        # Notify user
        await callback.message.answer(
            "✅ Ma'lumotlaringiz adminga yuborildi!\n"
            "Ko'rib chiqilgach, sizga javob beriladi.",
            reply_markup=get_main_menu()
        )

        # Save user ID (for admin response)
        user_id = callback.from_user.id
        await state.update_data(user_id=user_id)

        # Send application to admin
        caption = (
            "📋 Yangi hamkorlik so'rovi:\n\n"
            f"👤 Foydalanuvchi: @{callback.from_user.username or callback.from_user.full_name}\n"
            f"🆔 User ID: {user_id}\n\n"
            f"🏢 Tashkilot: {data['name']}\n"
            f"📞 Aloqa: {data['contact']}\n"
            f"📍 Manzil: {data['address']}\n\n"
            "Ma'lumotlarni tasdiqlaysizmi?"
        )

        admin_keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"admin_approve_{user_id}"),
                    types.InlineKeyboardButton(text="❌ Rad etish", callback_data=f"admin_reject_{user_id}")
                ]
            ]
        )

        await callback.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=data['license_photo'],
            caption=caption,
            reply_markup=admin_keyboard
        )

    elif callback.data == "confirm_no":
        await callback.message.answer(
            "❌ Ma'lumotlar bekor qilindi. Asosiy menyuga qaytdingiz.",
            reply_markup=get_main_menu()
        )

    await state.clear()


@router.callback_query(lambda c: c.data.startswith("admin_approve_") or c.data.startswith("admin_reject_"))
async def admin_decision(callback: types.CallbackQuery):
    """
    Step 7: Handle admin decision (approve/reject).
    - If approved → save application to DB and notify user
    - If rejected → notify user about rejection
    """
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Sizda ruxsat yo'q!")
        return

    decision = "approve" if "approve" in callback.data else "reject"
    user_id = int(callback.data.split("_")[-1])

    if decision == "approve":
        try:
            # Extract data from caption
            caption_text = callback.message.caption
            lines = caption_text.split('\n')

            name, contact, address = "", "", ""
            for line in lines:
                if "🏢 Tashkilot:" in line:
                    name = line.split("🏢 Tashkilot:")[1].strip()
                elif "📞 Aloqa:" in line:
                    contact = line.split("📞 Aloqa:")[1].strip()
                elif "📍 Manzil:" in line:
                    address = line.split("📍 Manzil:")[1].strip()

            # Save to database
            async with async_session() as session:
                new_application = Application(
                    full_name=name,
                    phone=contact,
                    pharmacy_name=address,
                    approved=True
                )
                session.add(new_application)
                await session.commit()
                app_id = new_application.id

            # Update admin message
            await callback.message.edit_caption(
                caption=callback.message.caption + f"\n\n✅ TASDIQLANDI (ID: {app_id})",
                reply_markup=None
            )

            # Notify user
            await callback.bot.send_message(
                chat_id=user_id,
                text=(
                    f"🎉 Tabriklaymiz! Hamkorlik so'rovingiz tasdiqlandi!\n"
                    f"📝 Ariza raqami: #{app_id}"
                )
            )

        except Exception as e:
            print(f"Database saving error: {e}")
            await callback.answer("❌ Error while saving to database!")

    elif decision == "reject":
        # Update admin message
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n❌ RAD ETILDI",
            reply_markup=None
        )

        # Notify user
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ Afsuski, hamkorlik so'rovingiz rad etildi.\n"
                "Batafsil ma'lumot uchun admin bilan bog'laning."
            )
        )

    await callback.answer()

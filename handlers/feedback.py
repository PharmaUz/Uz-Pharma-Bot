import os
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import async_session
from database.models import Comment

router = Router()

class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()

# --- Foydalanuvchi tugmani bosganda ---
@router.callback_query(lambda c: c.data == "feedback")
async def start_feedback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("🤝 Fikr bildiring\n\nIltimos, fikringizni yozib yuboring.")
    await state.set_state(FeedbackStates.waiting_for_feedback)


# --- Foydalanuvchi fikr yuborganda ---
@router.message(FeedbackStates.waiting_for_feedback)
async def receive_feedback(message: types.Message, state: FSMContext):
    feedback_text = message.text
    user_id = message.from_user.id

    # FSM ichiga vaqtincha saqlab qo‘yamiz
    await state.update_data(feedback_text=feedback_text, user_id=user_id)

    # Admin uchun tugmalar
    admin_id = int(os.getenv("ADMIN_ID"))
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="✅ Qabul qilish", callback_data=f"confirm_comment:{user_id}"
                ),
                types.InlineKeyboardButton(
                    text="❌ Rad etish", callback_data=f"reject_comment:{user_id}"
                ),
            ]
        ]
    )

    await message.bot.send_message(
        admin_id,
        f"Yangi fikr keldi:\n\n{feedback_text}\n\nFoydalanuvchi ID: {user_id}",
        reply_markup=keyboard
    )

    await message.answer("Fikringiz yuborildi va moderator tasdig‘ini kutmoqda.")
    await state.update_data(sent_to_admin=True)


# --- Admin qabul qilsa ---
@router.callback_query(lambda c: c.data.startswith("confirm_comment:"))
async def confirm_comment_handler(callback: types.CallbackQuery):
    try:
        _, user_id = callback.data.split(":")
        user_id = int(user_id)
    except ValueError:
        await callback.answer("❌ Callback data noto‘g‘ri keldi")
        return

    # Foydalanuvchining FSM state ma'lumotini olib kelamiz
    storage = callback.bot['fsm_storage']
    user_state = FSMContext(storage, chat_id=user_id, user_id=user_id)
    data = await user_state.get_data()

    feedback_text = data.get("feedback_text")
    if not feedback_text:
        await callback.answer("❌ Fikr topilmadi (FSM bo‘sh)")
        return

    # Bazaga yozamiz
    async with async_session() as session:
        comment = Comment(
            user_id=user_id,
            description=feedback_text,
        )
        session.add(comment)
        await session.commit()

    # Foydalanuvchi va adminni xabardor qilish
    await callback.bot.send_message(user_id, "✅ Fikringiz qabul qilindi!")
    await callback.answer("Fikr tasdiqlandi ✅", show_alert=True)

    await user_state.clear()


# --- Admin rad etsa ---
@router.callback_query(lambda c: c.data.startswith("reject_comment:"))
async def reject_comment_handler(callback: types.CallbackQuery):
    try:
        _, user_id = callback.data.split(":")
        user_id = int(user_id)
    except ValueError:
        await callback.answer("❌ Callback data noto‘g‘ri keldi")
        return

    await callback.bot.send_message(user_id,    "❌ Fikringiz rad etildi.")
    await callback.answer("Fikr rad etildi ❌", show_alert=True)

    # Foydalanuvchining state’ini tozalaymiz
    storage = callback.bot['fsm_storage']
    user_state = FSMContext(storage, chat_id=user_id, user_id=user_id)
    await user_state.clear()

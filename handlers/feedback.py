import os
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from keyboards.main_menu import get_main_menu, get_confirm_keyboard
from database.db import async_session
from database.models import Comment
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
ADMIN_ID = os.getenv("ADMIN_ID")
if ADMIN_ID is None:
    raise ValueError("ADMIN_ID not found in .env file!")
ADMIN_ID = int(ADMIN_ID)

router = Router()


class FeedbackForm(StatesGroup):
    """
    Feedback FSM states:
    - text: user enters feedback text
    - confirm: user confirms feedback before sending
    """
    text = State()
    confirm = State()


@router.callback_query(lambda c: c.data == "feedback")
async def start_feedback(callback: types.CallbackQuery, state: FSMContext):
    """
    Start feedback process.
    Asks the user to enter their feedback text.
    """
    await callback.message.answer("💬 Fikringizni kiriting:")
    await state.set_state(FeedbackForm.text)


@router.message(StateFilter(FeedbackForm.text))
async def process_feedback(message: types.Message, state: FSMContext):
    """
    Save user's feedback text and ask for confirmation.
    """
    await state.update_data(text=message.text)
    await message.answer(
        f"Fikringiz: \"{message.text}\"\n\nTasdiqlaysizmi?",
        reply_markup=get_confirm_keyboard()
    )
    await state.set_state(FeedbackForm.confirm)


@router.callback_query(StateFilter(FeedbackForm.confirm))
async def confirm_feedback(callback: types.CallbackQuery, state: FSMContext):
    """
    Handle user confirmation.
    If confirmed, feedback is sent to admin for approval.
    """
    data = await state.get_data()
    user = callback.from_user

    if callback.data == "confirm_yes":
        # Send feedback to admin with approve/reject buttons
        admin_keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="✅ Tasdiqlash",
                        callback_data=f"admin_feedback_approve_{user.id}"
                    ),
                    types.InlineKeyboardButton(
                        text="❌ Rad etish",
                        callback_data=f"admin_feedback_reject_{user.id}"
                    )
                ]
            ]
        )
        await callback.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"💬 Yangi fikr:\n\n"
                f"👤 @{user.username or user.full_name}\n"
                f"🆔 ID: {user.id}\n\n"
                f"\"{data['text']}\"\n\n"
                f"Tasdiqlaysizmi?"
            ),
            reply_markup=admin_keyboard
        )
        await callback.message.answer(
            "✅ Fikringiz adminga yuborildi!",
            reply_markup=get_main_menu()
        )
    else:
        await callback.message.answer(
            "❌ Fikringiz bekor qilindi.",
            reply_markup=get_main_menu()
        )

    await state.clear()


@router.callback_query(
    lambda c: c.data.startswith("admin_feedback_approve_")
    or c.data.startswith("admin_feedback_reject_")
)
async def admin_feedback_decision(callback: types.CallbackQuery):
    """
    Handle admin's decision (approve or reject feedback).
    - If approved → saves to database.
    - If rejected → notifies user.
    """
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Sizda ruxsat yo'q!")
        return

    action = "approve" if "approve" in callback.data else "reject"
    user_id = int(callback.data.split("_")[-1])

    # Extract comment text and username from admin's forwarded message
    lines = callback.message.text.split('\n')
    username = ""
    text = ""

    for line in lines:
        if line.startswith("👤"):
            username = line.split("👤 ")[1].strip()
        elif line.startswith("\"") and line.endswith("\""):
            text = line.strip("\"")

    if action == "approve":
        try:
            async with async_session() as session:
                new_comment = Comment(
                    user_id=user_id,
                    username=username,
                    text=text,
                    approved=True
                )
                session.add(new_comment)
                await session.commit()
                comment_id = new_comment.id

            # Update admin message
            await callback.message.edit_text(
                callback.message.text + f"\n\n✅ TASDIQLANDI (ID: {comment_id})",
                reply_markup=None
            )
            # Notify user
            await callback.bot.send_message(
                chat_id=user_id,
                text="✅ Fikringiz tasdiqlandi! Rahmat."
            )
        except Exception as e:
            print(f"Database error: {e}")
            await callback.answer("❌ Bazaga saqlashda xatolik!")
    else:
        # Reject feedback
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ RAD ETILDI",
            reply_markup=None
        )
        await callback.bot.send_message(
            chat_id=user_id,
            text="❌ Fikringiz rad etildi."
        )

    await callback.answer()

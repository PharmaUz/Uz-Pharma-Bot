# handlers/ai_assistant.py
import os
import re
import logging
import requests
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from typing import Dict, List

router = Router()
logger = logging.getLogger(__name__)


# API settings
API_KEY = os.getenv("GROQ_API_KEY")  # Enter your API key here
URL = "https://api.groq.com/openai/v1/chat/completions"
from datetime import datetime

# Daily question counter for each user
user_daily_limits: Dict[int, dict] = {}  
# Format: {user_id: {"date": "2025-09-12", "count": 5}}

DAILY_LIMIT = 5  # 5 questions per day

def check_daily_limit(user_id: int) -> bool:
    """
    Check if user hasn't exceeded today's limit
    """
    today = datetime.now().date().isoformat()
    
    if user_id not in user_daily_limits:
        user_daily_limits[user_id] = {"date": today, "count": 0}
    
    # Reset if it's a new day
    if user_daily_limits[user_id]["date"] != today:
        user_daily_limits[user_id] = {"date": today, "count": 0}
    
    # Check limit
    if user_daily_limits[user_id]["count"] >= DAILY_LIMIT:
        return False  # limit exceeded
    
    return True

def increment_daily_limit(user_id: int):
    """
    Increment counter when user asks a question
    """
    today = datetime.now().date().isoformat()
    if user_id not in user_daily_limits:
        user_daily_limits[user_id] = {"date": today, "count": 0}
    
    if user_daily_limits[user_id]["date"] != today:
        user_daily_limits[user_id] = {"date": today, "count": 0}
    
    user_daily_limits[user_id]["count"] += 1

# FSM states
class AIConsultState(StatesGroup):
    waiting_for_question = State()

# Conversation history for each user
user_conversations: Dict[int, List[dict]] = {}


def clean_ai_response(text: str) -> str:
    """
    Clean AI response for Telegram
    """
    if not text:
        return ""
    
    # Clean markdown formats
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)  # **bold** -> *bold*
    text = re.sub(r'###\s+(.*?)(?=\n|$)', r'📌 \1', text)  # ### Title -> 📌 Title
    text = re.sub(r'##\s+(.*?)(?=\n|$)', r'📋 \1', text)   # ## Title -> 📋 Title
    text = re.sub(r'#\s+(.*?)(?=\n|$)', r'📍 \1', text)    # # Title -> 📍 Title
    
    # Clean table format
    text = re.sub(r'\|.*?\|', '', text)  # Remove table rows
    text = re.sub(r'\|[-\s\|]+\|', '', text)  # Remove table separators
    
    # Reduce multiple empty lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Trim leading and trailing whitespace
    text = text.strip()
    
    return text

def escape_markdown(text: str) -> str:
    """
    Escape special characters for MarkdownV2
    """
    # Characters that need escaping in MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    # Escape each character
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def get_system_message():
    """
    Returns system message
    """
    return {
        "role": "system",
        "content": (
            "Siz tibbiyot bo'yicha yordamchi AI chatbotisiz. "
            "Faqat sog'liq, kasalliklar, simptomlar, davolash usullari haqida savollarga javob bering. "
            "O'zbek tilida tushunib, javob qaytaring. "
            "MUHIM: Javoblaringizni faqat oddiy matn formatida yozing. "
            "Hech qanday markdown belgilarini ishlatmang: *, **, _, __, #, |, `, []. "
            "Ro'yxat yozishda oddiy tire (-) yoki nuqta (•) ishlatib, har bir elementni yangi qatordan boshlang. "
            "Jadval o'rniga oddiy ro'yxat yozing. "
            "Matnni sodda, tushunarli va oddiy formatda yozing. "
            "Javoblaringizni iloji boricha qisqa, aniq va lo'nda yozing. "
            "Keraksiz tafsilotlarni yozmang, foydalanuvchi tez tushunadigan qilib yozing. "
            "Agar savol tibbiyot bilan bog'liq bo'lmasa, "
            "'Men faqat tibbiyotga oid savollarga javob bera olaman.' deb yozing."
        )
    }

def get_user_conversation_history(user_id: int) -> List[dict]:
    """
    Returns conversation history for user
    """
    if user_id not in user_conversations:
        user_conversations[user_id] = [get_system_message()]
    return user_conversations[user_id]

def clear_user_conversation(user_id: int):
    """
    Clears user conversation history
    """
    user_conversations[user_id] = [get_system_message()]

async def ask_groq(question: str, user_id: int) -> str:
    """
    Send question to Groq API and get response
    """
    conversation_history = get_user_conversation_history(user_id)
    
    # Add user question to history
    conversation_history.append({"role": "user", "content": question})

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "openai/gpt-oss-120b",
        "messages": conversation_history,
        "max_tokens": 450,
        "stop": None
    }

    try:
        response = requests.post(URL, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            
            # Clean response
            answer = clean_ai_response(answer)
            
            # Add response to history as well
            conversation_history.append({"role": "assistant", "content": answer})
            
            return answer
        else:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            return "Kechirasiz, hozir xizmatda muammo bor. Keyinroq urinib ko'ring."
    
    except requests.exceptions.Timeout:
        return "Javob kutish vaqti tugadi. Iltimos, qayta urinib ko'ring."
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return "Internet bilan bog'lanishda muammo. Keyinroq urinib ko'ring."
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "Kutilmagan xatolik yuz berdi. Keyinroq urinib ko'ring."

def get_ai_menu():
    """
    Returns AI consultation menu
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Savol berish", callback_data="ask_ai_question")],
            [InlineKeyboardButton(text="🗑️ Suhbatni tozalash", callback_data="clear_ai_chat")],
            [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="back_to_main")]
        ]
    )
    return keyboard

def get_back_keyboard():
    """
    Returns back keyboard
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 AI menyuga qaytish", callback_data="ai_consult")],
            [types.InlineKeyboardButton(
                text="🔍 Dorilarni qidirish",
                switch_inline_query_current_chat=""
            )]
        ]
    )
    return keyboard

@router.callback_query(lambda c: c.data == "ai_consult")
async def ai_consult_menu(callback: types.CallbackQuery):
    """
    Shows AI consultation menu
    """
    await callback.message.edit_text(
        "🤖 *AI Tibbiy Konsultatsiya*\n\n"
        "Men sizga tibbiyot bo'yicha savollaringizga javob bera olaman\\.\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=get_ai_menu(),
        parse_mode="MarkdownV2"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "ask_ai_question")
async def start_ai_question(callback: types.CallbackQuery, state: FSMContext):
    """
    Starts asking question to AI
    """
    await callback.message.edit_text(
        "💬 *Savolingizni yozing*\n\n"
        "Tibbiyot bilan bog'liq har qanday savolingizni yoza olasiz\\.\n"
        "Masalan: bosh og'rig'i, yurak kasalliklari, biror simptom haqida\\.\\.\\.\n\n"
        "⚠️ _Eslatma: Men faqat umumiy ma'lumot beraman\\. Aniq tashxis uchun doktorga murojaat qiling\\._",
        reply_markup=get_back_keyboard(),
        parse_mode="MarkdownV2"
    )
    await state.set_state(AIConsultState.waiting_for_question)
    await callback.answer()


def trim_incomplete_sentence(text: str) -> str:
    """
    Remove incomplete sentence at the end of text
    """
    if not text:
        return ""
    
    # Find where the last period, question or exclamation mark ends
    last_punct = max(text.rfind("."), text.rfind("?"), text.rfind("!"))
    
    if last_punct == -1:
        return text.strip()
    
    return text[:last_punct+1].strip()


def format_ai_response_for_telegram(text: str) -> str:
    """
    Format AI response beautifully for Telegram
    """
    if not text:
        return ""
    
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue
        
        # Format headers
        if any(keyword in line.lower() for keyword in ['sabab', 'belgi', 'simptom', 'davolash', 'tavsiya', 'usul']):
            if not line.startswith('•') and not line.startswith('-'):
                formatted_lines.append(f"🔹 <b>{line}</b>")
                continue
        
        # Format list elements
        if line.startswith('•') or line.startswith('-'):
            # Remove • or - and add emoji
            clean_line = line.lstrip('•- ').strip()
            formatted_lines.append(f"• {clean_line}")
            if line.startswith('*'):
                formatted_lines[-1] = f"• <b>{clean_line}</b>"
            continue
        # Highlight important information
        elif any(word in line.lower() for word in ['muhim', 'diqqat', 'eslatma', 'ogohlantirish']):
            formatted_lines.append(f"⚠️ <i>{line}</i>")
        # Regular lines
        else:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

@router.message(AIConsultState.waiting_for_question)
async def process_ai_question(message: types.Message, state: FSMContext):
    """
    Processes question sent to AI
    """
    user_id = message.from_user.id
    
    # Check limit
    if not check_daily_limit(user_id):
        await message.answer(
            f"⚠️ Siz bugun {DAILY_LIMIT} ta savol berdingiz. "
            "Ertaga yana urinib ko'ring."
        )
        return
    
    # If limit not exceeded → increment counter
    increment_daily_limit(user_id)

    user_question = message.text
    
    # Send "preparing response" message
    waiting_msg = await message.answer("🤖 Javob tayyorlanmoqda...")
    
    # Get response from AI
    ai_response = await ask_groq(user_question, user_id)

    # Clean and format response
    cleaned_response = clean_ai_response(ai_response)
    formatted_response = format_ai_response_for_telegram(cleaned_response)
    formatted_response = trim_incomplete_sentence(formatted_response)
    # Beautifully formatted response
    response_text = f"❓ <b>Savolingiz:</b>\n<i>{user_question}</i>\n\n"
    response_text += f"🤖 <b>AI javobi:</b>\n{formatted_response}\n\n"
    response_text += f"⚠️ <i>Bu ma'lumot faqat umumiy xarakterga ega. Aniq tashxis va davolash uchun doktorga murojaat qiling.</i>"
    
    # Send response
    try:
        await waiting_msg.edit_text(
            response_text,
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"HTML parsing failed: {e}")
        # If HTML parsing fails, use plain text
        simple_response = f"❓ Savolingiz:\n{user_question}\n\n🤖 AI javobi:\n{cleaned_response}\n\n⚠️ Bu ma'lumot faqat umumiy xarakterga ega. Aniq tashxis va davolash uchun doktorga murojaat qiling."
        try:
            await waiting_msg.edit_text(
                simple_response,
                reply_markup=get_back_keyboard()
            )
        except Exception as e2:
            logger.error(f"Failed to send response: {e2}")
            await waiting_msg.edit_text(
                "Javobda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",
                reply_markup=get_back_keyboard()
            )

@router.callback_query(lambda c: c.data == "clear_ai_chat")
async def clear_ai_conversation(callback: types.CallbackQuery):
    """
    Clears user conversation history
    """
    user_id = callback.from_user.id
    clear_user_conversation(user_id)
    
    await callback.message.edit_text(
        "✅ *Suhbat tarixi tozalandi\\!*\n\n"
        "Endi yangi suhbat boshlanadi\\. Eski savollar va javoblar eslab qolinmaydi\\.",
        reply_markup=get_ai_menu(),
        parse_mode="MarkdownV2"
    )
    await callback.answer("Suhbat tarixi tozalandi!")

@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    """
    Returns to main menu
    """
    from keyboards.main_menu import get_main_menu  # Import from your filter file
    
    await state.clear()
    await callback.message.edit_text(
        "🏥 *Farmatsiya Bot*\n\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=get_main_menu(),
        parse_mode="MarkdownV2"
    )
    await callback.answer()

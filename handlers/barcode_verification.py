# handlers/barcode_verification.py
import os
import io
import logging
import requests
import json
import warnings
import urllib3
from datetime import datetime
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Dict, Optional, Tuple


warnings.filterwarnings('ignore', message='Unverified HTTPS request')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import barcode libraries
try:
    from PIL import Image
    import cv2
    import numpy as np
    from pyzbar import pyzbar
except ImportError:
    Image = None
    cv2 = None
    np = None
    pyzbar = None

router = Router()
logger = logging.getLogger(__name__)

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
REQUEST_TIMEOUT = 30

# FSM states for barcode verification
class BarcodeVerificationState(StatesGroup):
    waiting_for_input = State()


def get_barcode_menu():
    """
    Returns barcode verification menu
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📷 Rasm yuklash", callback_data="upload_barcode_image")],
            [InlineKeyboardButton(text="🔢 Kod kiritish", callback_data="enter_barcode_code")],
            [InlineKeyboardButton(text="🔙 AI menyuga qaytish", callback_data="ai_consult")]
        ]
    )
    return keyboard


def validate_ean_checksum(code: str) -> bool:
    """
    Validate EAN-13 or EAN-8 checksum
    """
    if not code.isdigit():
        return False
    
    if len(code) not in [8, 13]:
        return False
    
    # Calculate checksum
    odd_sum = sum(int(code[i]) for i in range(0, len(code)-1, 2))
    even_sum = sum(int(code[i]) for i in range(1, len(code)-1, 2))
    
    if len(code) == 13:
        checksum = (10 - ((odd_sum + even_sum * 3) % 10)) % 10
    else:  # EAN-8
        checksum = (10 - ((odd_sum * 3 + even_sum) % 10)) % 10
    
    return checksum == int(code[-1])


def validate_upc_checksum(code: str) -> bool:
    """
    Validate UPC-A checksum
    """
    if not code.isdigit() or len(code) != 12:
        return False
    
    odd_sum = sum(int(code[i]) for i in range(0, 11, 2))
    even_sum = sum(int(code[i]) for i in range(1, 11, 2))
    checksum = (10 - ((odd_sum * 3 + even_sum) % 10)) % 10
    
    return checksum == int(code[-1])


def validate_barcode_format(code: str, barcode_type: str) -> Tuple[bool, str]:
    """
    Validate barcode format and checksum
    Returns (is_valid, error_message)
    """
    code = code.strip()
    
    if barcode_type in ['EAN13', 'EAN-13']:
        if validate_ean_checksum(code):
            return True, ""
        return False, "EAN-13 checksum yaroqsiz"
    
    elif barcode_type in ['EAN8', 'EAN-8']:
        if validate_ean_checksum(code):
            return True, ""
        return False, "EAN-8 checksum yaroqsiz"
    
    elif barcode_type in ['UPCA', 'UPC-A']:
        if validate_upc_checksum(code):
            return True, ""
        return False, "UPC-A checksum yaroqsiz"
    
    elif barcode_type in ['CODE128', 'Code128']:
        # CODE128 doesn't have a simple checksum validation
        return True, ""
    
    elif barcode_type in ['QRCODE', 'QR']:
        # QR codes don't have checksum validation at this level
        return True, ""
    
    return True, ""  # Unknown types pass for now


async def decode_barcode_from_image(image_bytes: bytes) -> Optional[Tuple[str, str]]:
    """
    Decode barcode from image bytes
    Returns (decoded_data, barcode_type) or None
    """
    if not all([Image, cv2, np, pyzbar]):
        logger.error("Required libraries not installed for barcode detection")
        return None
    
    try:
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Try to decode barcodes
        barcodes = pyzbar.decode(gray)
        
        if barcodes:
            # Return first barcode found
            barcode = barcodes[0]
            data = barcode.data.decode('utf-8')
            barcode_type = barcode.type
            return data, barcode_type
        
        return None
    except Exception as e:
        logger.error(f"Error decoding barcode: {e}")
        return None


async def query_uzpharm_api(code: str) -> Optional[Dict]:
    """
    Query UzPharm-Control API for drug information
    """
    try:
        url = "https://www.uzpharm-control.uz/registries/api_mpip/server-response.php?draw=1&start=0&length=5000"
        headers = {
            'Accept': 'application/json',
            'Accept-Charset': 'UTF-8',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
        
        content = response.content.decode('utf-8-sig')
        
        if response.status_code == 200:
            try:
                data = json.loads(content)
                if "data" in data:
                    for item in data["data"]:
                        cert_num = str(item.get("certificate_number", "")).strip()
                        if code in cert_num or cert_num in code:
                            cleaned_item = {}
                            for key, value in item.items():
                                if isinstance(value, str):
                                    cleaned_value = value.replace('\ufeff', '').strip()
                                    cleaned_item[key] = cleaned_value
                                else:
                                    cleaned_item[key] = value
                            return cleaned_item
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                logger.error(f"Raw response: {content[:200]}")
                return None
        
        return None
    except Exception as e:
        logger.error(f"UzPharm-Control API error: {e}")
        return None


def calculate_confidence_score(
    barcode_valid: bool,
    found_in_uzpharm: bool
) -> float:
    """
    Calculate confidence score based on validation results
    """
    score = 0.0
    
    if barcode_valid:
        score += 0.5
    
    if found_in_uzpharm:
        score += 0.5
    
    return min(score, 1.0)


def determine_authenticity(confidence: float) -> str:
    """
    Determine authenticity label based on confidence score
    """
    if confidence >= 0.7:
        return "✅ Haqiqiy"
    elif confidence >= 0.4:
        return "❓ Noma'lum"
    else:
        return "❌ Soxta"


def generate_explanation(
    barcode_valid: bool,
    found_in_uzpharm: bool,
    validation_error: str
) -> str:
    """
    Generate explanation for the verification result
    """
    reasons = []
    
    if not barcode_valid:
        reasons.append(f"❌ Checksum xato: {validation_error}")
    
    if not found_in_uzpharm:
        reasons.append("⚠️ UzPharm-Control bazasida topilmadi")
    
    if barcode_valid and found_in_uzpharm:
        reasons.append("✅ Ro'yxatdan o'tgan dori")
    
    return "\n".join(reasons) if reasons else "✅ Tekshiruv muvaffaqiyatli o'tdi"


def generate_recommendation(authenticity: str, confidence: float) -> str:
    """
    Generate recommendation based on authenticity
    """
    if "Haqiqiy" in authenticity:
        return "✅ Xavfsiz ishlatish mumkin"
    elif "Noma'lum" in authenticity:
        return "⚠️ Qo'shimcha tekshiruvdan o'tkazing yoki aniqroq rasm yuboring"
    else:
        return "🚫 Ishlatmang! Nazorat organlariga xabar bering"


async def verify_barcode(code: str, barcode_type: str = "UNKNOWN") -> Dict:
    """
    Main verification function
    """
    # Validate format
    is_valid, validation_error = validate_barcode_format(code, barcode_type)
    
    # Query UzPharm API
    uzpharm_data = await query_uzpharm_api(code)
    
    # Calculate confidence
    confidence = calculate_confidence_score(
        is_valid,
        uzpharm_data is not None
    )
    
    # Determine authenticity
    authenticity = determine_authenticity(confidence)
    
    # Generate explanation
    explanation = generate_explanation(
        is_valid,
        uzpharm_data is not None,
        validation_error
    )
    
    # Generate recommendation
    recommendation = generate_recommendation(authenticity, confidence)
    
    return {
        "code": code,
        "barcode_type": barcode_type,
        "authenticity": authenticity,
        "confidence": confidence,
        "explanation": explanation,
        "recommendation": recommendation,
        "uzpharm_data": uzpharm_data
    }


def format_verification_result(result: Dict) -> str:
    """
    Format verification result for Telegram
    """
    text = f"🔍 <b>Barcode Tekshiruv Natijasi</b>\n\n"
    text += f"📊 <b>Kod:</b> <code>{result['code']}</code>\n"
    text += f"🏷 <b>Turi:</b> {result['barcode_type']}\n\n"
    text += f"<b>Natija:</b> {result['authenticity']}\n"
    text += f"<b>Ishonch darajasi:</b> {result['confidence']:.0%}\n\n"
    text += f"<b>Tushuntirish:</b>\n{result['explanation']}\n\n"
    text += f"<b>Tavsiya:</b>\n{result['recommendation']}\n\n"
    
    if result['uzpharm_data']:
        data = result['uzpharm_data']
        text += f"\n<b>📦 Mahsulot ma'lumoti (UzPharm-Control):</b>\n"
        if data.get('medicine_name'):
            text += f"• Nomi: {data['medicine_name']}\n"
        if data.get('producer_name'):
            text += f"• Ishlab chiqaruvchi: {data['producer_name']}\n"
    
    text += f"\n<i>⏰ Tekshirilgan: {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>"
    
    return text


@router.callback_query(lambda c: c.data == "barcode_verify")
async def barcode_verify_menu(callback: types.CallbackQuery):
    """
    Shows barcode verification menu
    """
    await callback.message.edit_text(
        "🔍 <b>Barcode Tekshirish</b>\n\n"
        "Dori barcode yoki QR kodini tekshiring va asl yoki soxta ekanligini aniqlang.\n\n"
        "Quyidagi usullardan birini tanlang:",
        reply_markup=get_barcode_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "upload_barcode_image")
async def start_image_upload(callback: types.CallbackQuery, state: FSMContext):
    """
    Start image upload process
    """
    back_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="barcode_verify")]
        ]
    )
    
    await callback.message.edit_text(
        "📷 <b>Barcode rasmini yuboring</b>\n\n"
        "Barcode yoki QR kod tushirilgan rasmni yuboring.\n\n"
        "⚠️ <i>Rasm hajmi 10 MB dan oshmasligi kerak.</i>",
        reply_markup=back_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(BarcodeVerificationState.waiting_for_input)
    await state.update_data(input_type="image")
    await callback.answer()


@router.callback_query(lambda c: c.data == "enter_barcode_code")
async def start_code_entry(callback: types.CallbackQuery, state: FSMContext):
    """
    Start code entry process
    """
    back_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="barcode_verify")]
        ]
    )
    
    await callback.message.edit_text(
        "🔢 <b>Barcode kodini kiriting</b>\n\n"
        "Mahsulot barcode yoki ro'yxatdan o'tish kodini kiriting.\n\n"
        "Masalan: <code>4600702011074</code> yoki <code>DV/M 03662/02/21</code>",
        reply_markup=back_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(BarcodeVerificationState.waiting_for_input)
    await state.update_data(input_type="text")
    await callback.answer()


@router.message(BarcodeVerificationState.waiting_for_input, lambda message: message.photo)
async def process_barcode_image(message: types.Message, state: FSMContext):
    """
    Process uploaded barcode image
    """
    try:
        # Check if libraries are available
        if not all([Image, cv2, np, pyzbar]):
            await message.answer(
                "⚠️ Barcode skanerga kerakli kutubxonalar o'rnatilmagan.\n"
                "Iltimos, kod orqali tekshiring.",
                reply_markup=get_barcode_menu()
            )
            await state.clear()
            return
        
        # Get the largest photo
        photo = message.photo[-1]
        
        # Check file size
        if photo.file_size > MAX_FILE_SIZE:
            await message.answer(
                f"⚠️ Rasm hajmi juda katta ({photo.file_size / 1024 / 1024:.1f} MB).\n"
                f"Maksimal hajm: {MAX_FILE_SIZE / 1024 / 1024:.0f} MB",
                reply_markup=get_barcode_menu()
            )
            await state.clear()
            return
        
        # Download photo
        waiting_msg = await message.answer("🔄 Rasm tahlil qilinmoqda...")
        
        file = await message.bot.get_file(photo.file_id)
        file_bytes_io = await message.bot.download_file(file.file_path)
        image_bytes = file_bytes_io.getvalue()
        
        # Decode barcode
        result = await decode_barcode_from_image(image_bytes)
        
        if not result:
            await waiting_msg.edit_text(
                "❌ Rasmda barcode topilmadi.\n\n"
                "Iltimos, aniqroq rasm yuboring yoki kodni qo'lda kiriting.",
                reply_markup=get_barcode_menu()
            )
            await state.clear()
            return
        
        code, barcode_type = result
        
        # Verify barcode
        verification_result = await verify_barcode(code, barcode_type)
        
        # Format and send result
        result_text = format_verification_result(verification_result)
        
        await waiting_msg.edit_text(
            result_text,
            reply_markup=get_barcode_menu(),
            parse_mode="HTML"
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error processing barcode image: {e}")
        await message.answer(
            "❌ Rasm qayta ishlashda xatolik yuz berdi.\n"
            "Iltimos, boshqa rasm yuboring yoki kodni qo'lda kiriting.",
            reply_markup=get_barcode_menu()
        )
        await state.clear()


@router.message(BarcodeVerificationState.waiting_for_input, lambda message: message.text)
async def process_barcode_text(message: types.Message, state: FSMContext):
    """
    Process barcode code entered as text
    """
    try:
        code = message.text.strip()
        
        # Send processing message
        waiting_msg = await message.answer("🔄 Kod tekshirilmoqda...")
        
        # Verify barcode
        verification_result = await verify_barcode(code)
        
        # Format and send result
        result_text = format_verification_result(verification_result)
        
        await waiting_msg.edit_text(
            result_text,
            reply_markup=get_barcode_menu(),
            parse_mode="HTML"
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error processing barcode text: {e}")
        await message.answer(
            "❌ Kod tekshirishda xatolik yuz berdi.\n"
            "Iltimos, qayta urinib ko'ring.",
            reply_markup=get_barcode_menu()
        )
        await state.clear()

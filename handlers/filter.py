from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from database.db import async_session
from database.models import Drug
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(lambda c: c.data == "search_drug")
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
        "🏥 Dorilar qidiruv bo'limi\n"
        "Pastdagi tugmani bosing va dori nomini yozing 👇",
        reply_markup=keyboard
    )
    await callback.answer()


@router.inline_query()
async def inline_drug_search(inline_query: types.InlineQuery):
    """Search drugs in inline mode"""
    query = inline_query.query.strip().lower()
    
    try:
        async with async_session() as session:
            if query:
                # Search by drug name, category or manufacturer
                stmt = select(Drug).where(
                    or_(
                        Drug.name.ilike(f"%{query}%"),
                        Drug.category.ilike(f"%{query}%"),
                        Drug.manufacturer.ilike(f"%{query}%") if hasattr(Drug, 'manufacturer') else False
                    )
                ).limit(20)
            else:
                # If query is empty, just return the latest 10 drugs
                stmt = select(Drug).limit(10)

            result = await session.execute(stmt)
            drugs = result.scalars().all()
            
    except SQLAlchemyError as e:
        logger.error(f"Database error in drug search: {e}")
        drugs = []
    except Exception as e:
        logger.error(f"Unexpected error in drug search: {e}")
        drugs = []

    articles = []
    
    for drug in drugs:
        # Thumbnail image
        thumbnail = (
            getattr(drug, "thumbnail_url", None) or 
            getattr(drug, "image_url", None) or 
            "https://via.placeholder.com/150x150?text=Dori"
        )

        # Full information about the drug
        drug_info = f"💊 <b>{drug.name}</b>\n"

        if hasattr(drug, 'strength') and drug.strength:
            drug_info += f"📏 Miqdori: {drug.strength}\n"
        if hasattr(drug, 'manufacturer') and drug.manufacturer:
            drug_info += f"🏭 Ishlab chiqaruvchi: {drug.manufacturer}\n"
        if hasattr(drug, 'dosage_form') and drug.dosage_form:
            drug_info += f"📋 Shakli: {drug.dosage_form}\n"
        if hasattr(drug, 'price') and drug.price and drug.price > 0:
            drug_info += f"💰 Narxi: {drug.price:,} so'm\n"
        
        if hasattr(drug, 'prescription_required') and drug.prescription_required:
            drug_info += "⚠️ Retsept talab etiladi\n"
        
        if hasattr(drug, 'category') and drug.category:
            drug_info += f"🏷️ Kategoriya: {drug.category}\n"
        
        if hasattr(drug, 'description') and drug.description:
            description = drug.description[:200] + "..." if len(drug.description) > 200 else drug.description
            drug_info += f"\n📝 Tavsif: {description}"

        title = drug.name
        if hasattr(drug, 'strength') and drug.strength:
            title += f" ({drug.strength})"

        description_parts = []
        if hasattr(drug, 'manufacturer') and drug.manufacturer:
            description_parts.append(drug.manufacturer)
        if hasattr(drug, 'price') and drug.price and drug.price > 0:
            description_parts.append(f"{drug.price:,} so'm")

        description = " • ".join(description_parts)

        # Create inline keyboard for each drug with "Add to Cart" button
        drug_keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(
                    text="➕ Savatga qo'shish",
                    callback_data=f"add_to_cart:{drug.id}"
                )]
            ]
        )

        articles.append(
            InlineQueryResultArticle(
                id=str(drug.id),
                title=title,
                description=description,
                thumbnail_url=thumbnail,
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"<b>{drug.name}</b>\n\n"
                        f"<a href='{thumbnail}'>\u200b</a>"   # Display image in result
                        f"{drug_info}"
                    ),
                    parse_mode="HTML"
                ),
                reply_markup=drug_keyboard
            )
        )

    if not articles and query:
        articles.append(
            InlineQueryResultArticle(
                id="no_results",
                title="🚫 Natija topilmadi",
                description=f"'{query}' bo'yicha dorilar topilmadi",
                thumbnail_url="https://via.placeholder.com/150x150?text=Natija+Yo%27q",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"🚫 **Search Results**\n\n"
                        f"No drugs found for '{query}'.\n\n"
                        f"💡 Tips:\n"
                        f"• Make sure the drug name is spelled correctly\n"
                        f"• Try using abbreviations\n"
                        f"• Enter the category name\n"
                        f"• Enter the manufacturer name"
                    ),
                    parse_mode="Markdown"
                )
            )
        )

    try:
        await inline_query.answer(
            results=articles,
            cache_time=30,
            is_personal=False
        )
    except Exception as e:
        logger.error(f"Error answering inline query: {e}")
        await inline_query.answer(results=[], cache_time=5)

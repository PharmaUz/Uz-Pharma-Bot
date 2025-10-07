import logging

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError

from database.db import async_session
from database.models import Drug

router = Router()
logger = logging.getLogger(__name__)


@router.inline_query()
async def inline_drug_search(inline_query: types.InlineQuery):
    """
    Search drugs in inline mode.

    Args:
        inline_query (types.InlineQuery): Inline query object with user input.
    """
    query = inline_query.query.strip().lower()

    try:
        async with async_session() as session:
            if query:
                # Search by drug name, category, or manufacturer
                stmt = select(Drug).where(
                    or_(
                        Drug.name.ilike(f"%{query}%"),
                        Drug.category.ilike(f"%{query}%"),
                        Drug.manufacturer.ilike(f"%{query}%")
                        if hasattr(Drug, "manufacturer") else False
                    )
                ).limit(20)
            else:
                # If query is empty, return latest 10 drugs
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
        # Thumbnail image fallback
        thumbnail = (
            getattr(drug, "thumbnail_url", None)
            or getattr(drug, "image_url", None)
            or "https://via.placeholder.com/150x150?text=Dori"
        )

        # Full information about the drug
        drug_info = f"💊 <b>{drug.name}</b>\n"

        if getattr(drug, "strength", None):
            drug_info += f"📏 Miqdori: {drug.strength}\n"
        if getattr(drug, "manufacturer", None):
            drug_info += f"🏭 Ishlab chiqaruvchi: {drug.manufacturer}\n"
        if getattr(drug, "dosage_form", None):
            drug_info += f"📋 Shakli: {drug.dosage_form}\n"
        if getattr(drug, "price", 0) > 0:
            drug_info += f"💰 Narxi: {drug.price:,} so'm\n"

        if getattr(drug, "prescription_required", False):
            drug_info += "⚠️ Retsept talab etiladi\n"

        if getattr(drug, "category", None):
            drug_info += f"🏷️ Kategoriya: {drug.category}\n"

        if getattr(drug, "description", None):
            description = (
                drug.description[:200] + "..."
                if len(drug.description) > 200 else drug.description
            )
            drug_info += f"\n📝 Tavsif: {description}"

        # Title and description for inline query
        title = drug.name
        if getattr(drug, "strength", None):
            title += f" ({drug.strength})"

        description_parts = []
        if getattr(drug, "manufacturer", None):
            description_parts.append(drug.manufacturer)
        if getattr(drug, "price", 0) > 0:
            description_parts.append(f"{drug.price:,} so'm")

        description = " • ".join(description_parts)

        # Inline keyboard: Add to Cart button
        drug_keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="➕ Savatga qo'shish",
                        callback_data=f"add_to_cart:{drug.id}"
                    )
                ]
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
                        f"<a href='{thumbnail}'>\u200b</a>"
                        f"{drug_info}"
                    ),
                    parse_mode="HTML"
                ),
                reply_markup=drug_keyboard
            )
        )

    # No results case
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

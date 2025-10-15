import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import LabeledPrice, PreCheckoutQuery, ContentType

BOT_TOKEN = os.getenv("BOT_TOKEN")

CLICK_PROVIDER_TOKEN = os.getenv("CLICK_PROVIDER_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(lambda msg: msg.text == "/start")
async def start(message: types.Message):
    await message.answer("Salom! Click to‘lovni test qilish uchun /pay ni bosing 😊")

@dp.message(lambda msg: msg.text == "/pay")
async def pay(message: types.Message):
    prices = [LabeledPrice(label="Premium obuna (1 oy)", amount=500000)]  # 5000 so‘m
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Premium obuna",
        description="1 oylik obuna uchun to‘lov",
        payload="invoice_001",
        provider_token=CLICK_PROVIDER_TOKEN,
        currency="UZS",
        prices=prices,
        start_parameter="test-payment",
    )

@dp.pre_checkout_query()
async def checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(lambda msg: msg.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def got_payment(message: types.Message):
    payment = message.successful_payment
    amount = payment.total_amount / 100
    await message.answer(f"✅ To‘lov muvaffaqiyatli amalga oshirildi!\nSummasi: {amount} {payment.currency}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

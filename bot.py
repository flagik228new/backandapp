from aiogram import Bot, Dispatcher, F
from aiogram.types import LabeledPrice, Message
from aiogram.enums import ContentType
import asyncio
import aiohttp
import os

BOT_TOKEN = "8423828272:AAHGuxxQEvTELPukIXl2eNL3p25fI9GGx0U"
BACKEND_URL = os.getenv("BACKEND_URL")
if not BACKEND_URL:
    raise RuntimeError("BACKEND_URL is not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def create_stars_invoice(user_id: int, title: str, payload: str, price_stars: int) -> str:
    prices = [LabeledPrice(label=title, amount=price_stars)]

    msg = await bot.send_invoice(
        chat_id=user_id,
        title=title,
        description=title,
        payload=payload,
        currency="XTR",  # ⭐ ОБЯЗАТЕЛЬНО
        prices=prices
    )

    return msg.invoice_slug


@dp.message(F.successful_payment)
async def on_successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload

    async with aiohttp.ClientSession() as session:
        await session.post(
            f"{BACKEND_URL}/api/vpn/payment-success",
            params={"payload": payload}
        )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
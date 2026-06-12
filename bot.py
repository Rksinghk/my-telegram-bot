import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Railway ke Variables se Token uthane ka code
API_TOKEN = os.getenv('API_TOKEN')

# Agar token na mile toh error dikhaye
if not API_TOKEN:
    raise ValueError("API_TOKEN environment variable is missing!")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    # Banner image ka URL
    photo_url = "https://example.com/your-banner.jpg"
    
    caption = (
        f"👋 **HELLOW, {message.from_user.full_name}!**\n\n"
        "💐 **WELCOME TO UPI EARNING**\n\n"
        "📲 **JOIN 5 REQUIRED CHANNEL AND GET ₹400**\n\n"
        "🔒 **MUST JOIN ALL CHANNEL TO UNLOCK BOT.**\n\n"
        "✅ **AFTER JOINING CLICK VERIFY**"
    )

    # Inline Buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="JOIN 1", url="https://t.me/your_channel1"),
         InlineKeyboardButton(text="JOIN 2", url="https://t.me/your_channel2")],
        [InlineKeyboardButton(text="JOIN 3", url="https://t.me/your_channel3"),
         InlineKeyboardButton(text="JOIN 4", url="https://t.me/your_channel4")],
        [InlineKeyboardButton(text="✅ Verify", callback_data="verify")]
    ])

    await bot.send_photo(chat_id=message.chat.id, photo=photo_url, caption=caption, reply_markup=keyboard, parse_mode="Markdown")

async def main():
    print("Bot polling started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

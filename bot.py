import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Logs setup karna taaki pata chale bot kya kar raha hai
logging.basicConfig(level=logging.INFO)

# Railway ke Variables se Token uthana
API_TOKEN = os.getenv('API_TOKEN')

if not API_TOKEN:
    logging.error("API_TOKEN variable missing in Railway!")
    exit(1)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    # Banner image ka URL (aap isse change kar sakte hain)
    photo_url = "https://images.unsplash.com/photo-1633158829585-23ba8f7c8caf?q=80&w=500&auto=format&fit=crop"
    
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

    await bot.send_photo(
        chat_id=message.chat.id, 
        photo=photo_url, 
        caption=caption, 
        reply_markup=keyboard, 
        parse_mode="Markdown"
    )

async def main():
    logging.info("Bot polling started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

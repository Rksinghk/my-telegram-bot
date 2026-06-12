import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Logs setup
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
    # Banner image ka URL
    photo_url = "https://images.unsplash.com/photo-1633158829585-23ba8f7c8caf?q=80&w=500&auto=format&fit=crop"
    
    # Aapki di gayi text
    caption = (
        "🔺 **Welcome to X Files Bot!** 🔺\n\n"
        "🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹🔹\n\n"
        "⏰ **Search and access exclusive files easily.**\n"
        "🟡 **Download content with fast speed** 🔄\n"
        "📌 **Ready for an amazing show✨ From the latest releases to timeless classics, we've got something for everyone!**\n"
        "💠  🔛 **Safe, And Secure** 🔒 💠\n\n"
        "➖➖➖➖➖➖➖➖➖➖➖\n\n"
        "📲 **JOIN REQUIRED CHANNELS TO UNLOCK BOT.**\n"
        "✅ **AFTER JOINING CLICK VERIFY**"
    )

    # Inline Buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="JOIN 1", url="https://t.me/your_channel1"),
         InlineKeyboardButton(text="JOIN 2", url="https://t.me/your_channel2")],
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

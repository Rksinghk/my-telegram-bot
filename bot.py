import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Apna API Token yahan dalein
API_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Welcome Message aur Buttons
@dp.message(Command("start"))
async def start(message: types.Message):
    # Banner image ka URL (aap yahan apna direct image link dal sakte hain)
    photo_url = "https://example.com/your-banner.jpg"
    
    caption = (
        "👋 **HELLOW, {}!**\n\n"
        "💐 **WELCOME TO UPI EARNING**\n\n"
        "📲 **JOIN 5 REQUIRED CHANNEL AND GET ₹400**\n\n"
        "🔒 **MUST JOIN ALL CHANNEL TO UNLOCK BOT.**\n\n"
        "✅ **AFTER JOINING CLICK VERIFY**"
    ).format(message.from_user.full_name)

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
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

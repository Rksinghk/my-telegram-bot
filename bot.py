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
    
    # Aapka naya text
    caption = (
        f"✦ 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 {message.from_user.first_name} ✦\n\n"
        "❖ 𝙲𝚘𝚖𝚙𝚕𝚎𝚝𝚎 𝚂𝚒𝚖𝚙𝚕𝚎 𝚃𝚊𝚜𝚔\n"
        "☯  𝙴𝚊𝚛𝚗 ₹𝟺𝟶𝟶 𝚁𝚎𝚠𝚊𝚛𝚍\n"
        "〄 𝙹𝚘𝚒𝚗 𝟻 𝙾𝚏𝚏𝚒𝚌𝚒𝚊𝚕 𝙲𝚑𝚊𝚗𝚗𝚎𝚕𝚜\n"
        "⚿  𝚄𝚗𝚕𝚘𝚌𝚔 𝙱𝚘𝚝 𝙰𝚌𝚌𝚎𝚜𝚜\n"
        "☑  𝚃𝚊𝚙 𝚅𝚎𝚛𝚒𝚏𝚢 𝙰𝚏𝚝𝚎𝚛 𝙹𝚘𝚒𝚗𝚒𝚗𝚐\n\n"
        "⚶ 𝐑𝐞𝐰𝐚𝐫𝐝 𝐖𝐚𝐢𝐭𝐢𝐧𝐠 𝐅𝐨𝐫 𝐘𝐨𝐮 ⚶"
    )

    # Inline Buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➲ 𝐕𝐄𝐑𝐈𝐅𝐘 𝐍𝐎𝐖 ⟳♼", callback_data="verify")]
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

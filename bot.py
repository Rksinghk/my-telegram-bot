import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

logging.basicConfig(level=logging.INFO)
API_TOKEN = os.getenv('API_TOKEN')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Channel IDs (Channel ka username ya ID yahan dalein)
CHANNELS = ["@Moneyearning_updates", "@your_channel2_username"] # channel2 ka username ho toh better hai

@dp.message(Command("start"))
async def start(message: types.Message):
    caption = (
        f"✦ 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 {message.from_user.first_name} ✦\n\n"
        "❖ 𝙲𝚘𝚖𝚙𝚕𝚎𝚝𝚎 𝚂𝚒𝚖𝚙𝚕𝚎 𝚃𝚊𝚜𝚔\n"
        "☯  𝙴𝚊𝚛𝚗 ₹𝟺𝟶𝟶 𝚁𝚎𝚠𝚊𝚛𝚍\n"
        "〄 𝙹𝚘𝚒𝚗 𝟻 𝙾𝚏𝚏𝚒𝚌𝚒𝚊𝚕 𝙲𝚑𝚊𝚗𝚗𝚎𝚕𝚜\n"
        "⚿  𝚄𝚗𝚕𝚘𝚌𝚔 𝙱𝚘𝚝 𝙰𝚌𝚌𝚎𝚜𝚜\n"
        "☑  𝚃𝚊𝚙 𝚅𝚎𝚛𝚒𝚏𝚢 𝙰𝚏𝚝𝚎𝚛 𝙹𝚘𝚒𝚗𝚒𝚗𝚐"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="JOIN 1", url="https://t.me/Moneyearning_updates")],
        [InlineKeyboardButton(text="JOIN 2", url="https://t.me/+L4ubY08PrhtmZDI9")],
        [InlineKeyboardButton(text="➲ 𝐕𝐄𝐑𝐈𝐅𝐘 𝐍𝐎𝐖 ⟳♼", callback_data="verify")]
    ])
    await bot.send_photo(chat_id=message.chat.id, photo="https://images.unsplash.com/photo-1633158829585-23ba8f7c8caf?q=80&w=500", caption=caption, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(F.data == "verify")
async def verify(call: CallbackQuery):
    is_member = True
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=call.from_user.id)
            if member.status in ['left', 'kicked']:
                is_member = False
                break
        except Exception as e:
            logging.error(f"Error checking channel {channel}: {e}")
            is_member = False

    if is_member:
        await call.answer("✅ Verified! Access Granted.", show_alert=True)
        await call.message.answer("🎉 Aapka verification pura hua! Ab aap bot use kar sakte hain.")
    else:
        await call.answer("❌ Please join both channels first!", show_alert=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import os
import sqlite3
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.storage.memory import MemoryStorage

# Logging set-up
logging.basicConfig(level=logging.INFO)

# Config - Railway variables se values lein
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6897212040"))
# GitHub Pages ki live link yahan dalen
WEB_APP_URL = "https://rksinghk.github.io/my-telegram-bot/" 

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Database connection
def get_db():
    conn = sqlite3.connect("users.db", check_same_thread=False)
    return conn

# Database init
conn = get_db()
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance REAL DEFAULT 0.0,
        refer_by INTEGER
    )
""")
conn.commit()
conn.close()

# Start command
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    ref_id = args[1] if len(args) > 1 else None
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, refer_by) VALUES (?, ?)", (user_id, ref_id))
    conn.commit()
    conn.close()

    # Dashboard open karne ka button
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Open Bexa Premium Dashboard", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    
    await message.answer(
        "✨ *Welcome to Bexa Premium Earning Engine!*\n\n"
        "Dashboard open karne ke liye niche button par click karein.",
        reply_markup=keyboard, parse_mode="Markdown"
    )

# Withdraw function
@dp.message(Command("withdraw"))
async def withdraw_cmd(message: types.Message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    res = cursor.fetchone()
    conn.close()
    
    if res and res[0] >= 100:
        await message.answer("🏦 *Withdrawal Request Submitted!* Admin jald hi verify karega.")
        await bot.send_message(ADMIN_ID, f"💸 *New Payout Request*\nUser: `{message.from_user.id}`\nAmount: ₹{res[0]}", parse_mode="Markdown")
    else:
        await message.answer("❌ *Insufficient Balance!* Minimum ₹100 hone chahiye.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.storage.memory import MemoryStorage

# Config
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6897212040"))
WEB_APP_URL = "https://rksinghk.github.io/my-telegram-bot/" 

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Database Setup
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, refer_by INTEGER)")
conn.commit()

# --- Handlers ---

@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    
    # Referral System
    if len(args) > 1:
        ref_id = args[1]
        cursor.execute("INSERT OR IGNORE INTO users (user_id, refer_by) VALUES (?, ?)", (user_id, ref_id))
    else:
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

    # Dashboard Button
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Open Dashboard", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    await message.answer("✅ Welcome to Earning Bot!\nDashboard kholne ke liye niche button dabayein.", reply_markup=keyboard)

@dp.message(Command("withdraw"))
async def withdraw_cmd(message: types.Message):
    # Withdraw Logic
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    res = cursor.fetchone()
    if res and res[0] >= 10:
        await message.answer("🏦 Withdraw request admin ko bhej di gayi hai!")
        await bot.send_message(ADMIN_ID, f"💸 New Withdrawal Request from {message.from_user.id}")
    else:
        await message.answer("❌ Minimum ₹10 balance hona chahiye!")

async def main():
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())                       

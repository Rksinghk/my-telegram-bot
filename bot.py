import os
import sqlite3
import random
import time
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Logging
logging.basicConfig(level=logging.INFO)

# Config
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6897212040"))
PHOTO_URL = "https://i.postimg.cc/02GRzWDB/file-00000000d74071fa86d1d103d4ac7342.png"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Database
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    bonus_time INTEGER DEFAULT 0
)
""")
conn.commit()

CHANNELS = ["@Moneyearning_updates", "@bexamoneygroup"]

# FSM
class WithdrawState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_upi = State()

# --- Menus ---
def main_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🕹 Play"), KeyboardButton(text="👥 Refer")],
        [KeyboardButton(text="🎁 Daily Bonus"), KeyboardButton(text="📢 Tasks")],
        [KeyboardButton(text="⭐ Balance"), KeyboardButton(text="💳 Withdraw")]
    ], resize_keyboard=True)

# --- Functions ---
async def check_join(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ['left', 'kicked']: return False
        except: return False
    return True

# --- Handlers ---
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

    if not await check_join(user_id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➜ 𝗝𝗼𝗶𝗻 𝟭", url="https://t.me/Moneyearning_updates"),
             InlineKeyboardButton(text="➜ 𝗝𝗼𝗶𝗻 𝟮", url="https://t.me/bexamoneygroup")],
            [InlineKeyboardButton(text="➲ 𝐕𝐄𝐑𝐈𝐅𝐘", callback_data="verify")]
        ])
        await message.answer_photo(photo=PHOTO_URL, caption="⚠️ Join channels to unlock!", reply_markup=keyboard)
    else:
        await message.answer("✅ Welcome Back!", reply_markup=main_menu())

@dp.callback_query(F.data == "verify")
async def verify(call: CallbackQuery):
    if await check_join(call.from_user.id):
        await call.message.answer("✅ Success! Bot Unlocked.", reply_markup=main_menu())
    else:
        await call.answer("❌ Join both channels first!", show_alert=True)

@dp.message(F.text == "⭐ Balance")
async def balance(message: types.Message):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    res = cursor.fetchone()
    user_bal = res[0] if res else 0
    locked_bal = 500
    
    text = (
        f"📊 --- ACCOUNT SUMMARY ---\n\n"
        f"💰 Available Balance: ₹{user_bal}\n"
        f"🔒 Locked Balance: ₹{locked_bal}\n\n"
        f"🏧 Withdraw available from: ₹{user_bal + locked_bal}"
    )
    await message.answer(text)

@dp.message(F.text == "💳 Withdraw")
async def withdraw_start(message: types.Message, state: FSMContext):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    bal = cursor.fetchone()[0]
    if bal < 10:
        await message.answer("❌ Minimum Withdraw ₹10 is required.")
        return
    await state.set_state(WithdrawState.waiting_for_amount)
    await message.answer("💸 Enter Withdraw Amount:")

# (Baki logic waisa hi rahega jaisa purane code mein tha)

@dp.message(F.text == "🎁 Daily Bonus")
async def bonus(message: types.Message):
    now = int(time.time())
    cursor.execute("SELECT bonus_time FROM users WHERE user_id=?", (message.from_user.id,))
    data = cursor.fetchone()
    if data and (now - data[0] < 86400):
        await message.answer("⏳ Try again in 24 hours.")
    else:
        reward = random.randint(1, 5)
        cursor.execute("UPDATE users SET balance = balance + ?, bonus_time=? WHERE user_id=?", (reward, now, message.from_user.id))
        conn.commit()
        await message.answer(f"🎁 Bonus Added: ₹{reward}")

if __name__ == "__main__":
    asyncio.run(main())

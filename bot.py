import os
import sqlite3
import random
import time
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Logging Setup
logging.basicConfig(level=logging.INFO)

# Config
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 6897212040))

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Database Setup
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    referred_by INTEGER,
    bonus_time INTEGER DEFAULT 0,
    upi TEXT
)
""")
conn.commit()

# Channels
CHANNELS = ["@Moneyearning_updates", "@earn_dailyrewards"]

# FSM
class WithdrawState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_upi = State()

# --- Functions ---
def main_menu():
    keyboard = [
        [types.KeyboardButton(text="💰 Balance"), types.KeyboardButton(text="👥 Refer")],
        [types.KeyboardButton(text="🎁 Daily Bonus"), types.KeyboardButton(text="📢 Tasks")],
        [types.KeyboardButton(text="🏧 Withdraw")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

async def check_join(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]: return False
        except: return False
    return True

# --- Handlers ---
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

    if not await check_join(user_id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➜ 𝗝𝗼𝗶𝗻 𝟭", url="https://t.me/Moneyearning_updates"),
             InlineKeyboardButton(text="➜ 𝗝𝗼𝗶𝗻 𝟮", url="https://t.me/earn_dailyrewards")],
            [InlineKeyboardButton(text="➲ 𝐕𝐄𝐑𝐈𝐅𝐘", callback_data="verify")]
        ])
        await message.answer_photo(
            photo="https://images.unsplash.com/photo-1633158829585-23ba8f7c8caf?q=80&w=500",
            caption="⚠️ Join channels to unlock the bot!",
            reply_markup=keyboard
        )
    else:
        await message.answer("✅ Welcome Back!", reply_markup=main_menu())

@dp.callback_query(F.data == "verify")
async def verify(call: CallbackQuery):
    if await check_join(call.from_user.id):
        await call.message.answer("🎉 Verification Success!", reply_markup=main_menu())
    else:
        await call.answer("❌ Join both channels first!", show_alert=True)

@dp.message(F.text == "💰 Balance")
async def balance(message: types.Message):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    bal = cursor.fetchone()[0]
    await message.answer(f"💰 Your Balance: ₹{bal}")

@dp.message(F.text == "🎁 Daily Bonus")
async def bonus(message: types.Message):
    now = int(time.time())
    cursor.execute("SELECT bonus_time FROM users WHERE user_id=?", (message.from_user.id,))
    last_bonus = cursor.fetchone()[0]
    if now - last_bonus < 86400:
        await message.answer(f"⏳ Try again in {86400 - (now - last_bonus) // 3600} hours")
    else:
        reward = random.randint(1, 5)
        cursor.execute("UPDATE users SET balance = balance + ?, bonus_time=? WHERE user_id=?", (reward, now, message.from_user.id))
        conn.commit()
        await message.answer(f"🎁 Bonus Added: ₹{reward}")

@dp.message(F.text == "🏧 Withdraw")
async def withdraw_start(message: types.Message, state: FSMContext):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    bal = cursor.fetchone()[0]
    if bal < 10:
        await message.answer("❌ Min withdraw ₹10")
        return
    await state.set_state(WithdrawState.waiting_for_amount)
    await message.answer("💸 Enter Amount:")

@dp.message(WithdrawState.waiting_for_amount)
async def get_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("Enter number only")
    await state.update_data(amount=message.text)
    await state.set_state(WithdrawState.waiting_for_upi)
    await message.answer("🏦 Send UPI ID:")

@dp.message(WithdrawState.waiting_for_upi)
async def get_upi(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = int(data['amount'])
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, message.from_user.id))
    conn.commit()
    await bot.send_message(ADMIN_ID, f"💸 Withdraw Request\nUser: {message.from_user.id}\nAmt: {amount}\nUPI: {message.text}")
    await message.answer("✅ Request Sent!")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

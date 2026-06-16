import os
import sqlite3
import random
import time
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# =========================
# CONFIGURATION
# =========================
# Railway ke Variables mein API_TOKEN aur ADMIN_ID dalen
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 6897212040))

# =========================
# BOT SETUP
# =========================
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# =========================
# DATABASE
# =========================
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

# =========================
# CONSTANTS
# =========================
PHOTO_URL = "https://i.postimg.cc/02GRzWDB/file-00000000d74071fa86d1d103d4ac7342.png"
CHANNELS = [
    ("Money Earning Updates", "https://t.me/Moneyearning_updates", "@Moneyearning_updates"),
    ("Earn Daily Rewards", "https://t.me/earn_dailyrewards", "@earn_dailyrewards"),
]

# =========================
# FUNCTIONS
# =========================
async def check_join(user_id):
    for name, link, username in CHANNELS:
        try:
            member = await bot.get_chat_member(username, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("💰 Balance"), KeyboardButton("👥 Refer"))
    kb.add(KeyboardButton("🎁 Daily Bonus"), KeyboardButton("📢 Tasks"))
    kb.add(KeyboardButton("🏧 Withdraw"))
    return kb

# =========================
# FSM STATES
# =========================
class WithdrawState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_upi = State()

# =========================
# HANDLERS
# =========================
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        referred_by = None
        if args:
            try:
                referred_by = int(args)
                if referred_by != user_id:
                    cursor.execute("UPDATE users SET balance = balance + 10 WHERE user_id=?", (referred_by,))
                    conn.commit()
            except: pass
        cursor.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))
        conn.commit()

    joined = await check_join(user_id)
    if not joined:
        keyboard = InlineKeyboardMarkup(row_width=2)
        for i, channel in enumerate(CHANNELS):
            keyboard.insert(InlineKeyboardButton(text=f"📢 JOIN {i+1}", url=channel[1]))
        keyboard.add(InlineKeyboardButton(text="✅ VERIFY", callback_data="verify"))
        
        text = f"👋 HELLO, {message.from_user.first_name}\n\n💸 WELCOME TO REAL MONEY EARNING BOT\n\n📢 JOIN BOTH CHANNELS\n\n🔓 UNLOCK BOT AFTER VERIFY"
        await bot.send_photo(chat_id=message.chat.id, photo=PHOTO_URL, caption=text, reply_markup=keyboard)
        return

    await message.answer("✅ Welcome Back!", reply_markup=main_menu())

@dp.callback_query_handler(lambda c: c.data == "verify")
async def verify(call: types.CallbackQuery):
    if await check_join(call.from_user.id):
        await call.message.answer("✅ Verification Successful!\n\n🎉 Bot Unlocked.", reply_markup=main_menu())
    else:
        await call.answer("❌ Join both channels first", show_alert=True)

@dp.message_handler(lambda message: message.text == "💰 Balance")
async def balance(message: types.Message):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    data = cursor.fetchone()
    await message.answer(f"💰 Your Balance: ₹{data[0] if data else 0}")

@dp.message_handler(lambda message: message.text == "👥 Refer")
async def refer(message: types.Message):
    ref_link = f"https://t.me/real_moneyearning_bot?start={message.from_user.id}"
    await message.answer(f"👥 YOUR REFERRAL LINK\n\n{ref_link}\n\n🎁 Earn ₹10 Per Refer")

@dp.message_handler(lambda message: message.text == "🎁 Daily Bonus")
async def bonus(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT bonus_time FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()
    now = int(time.time())
    if data and (now - data[0] < 86400):
        left = 86400 - (now - data[0])
        await message.answer(f"⏳ Bonus already claimed\n\nTry again in {left // 3600} hours")
        return
    reward = random.randint(1, 5)
    cursor.execute("UPDATE users SET balance = balance + ?, bonus_time=? WHERE user_id=?", (reward, now, user_id))
    conn.commit()
    await message.answer(f"🎁 Daily Bonus Added: ₹{reward}")

@dp.message_handler(lambda message: message.text == "📢 Tasks")
async def tasks(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("🔥 Myntra Loot", url="https://myntr.it/dfDWkLZ"))
    keyboard.add(InlineKeyboardButton("💸 Flipkart Offer", url="https://fktr.in/XPOK63N"))
    await message.answer("🔥 COMPLETE TASKS & SHOP USING LINKS", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "🏧 Withdraw")
async def withdraw(message: types.Message, state: FSMContext):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    data = cursor.fetchone()
    if not data or data[0] < 10:
        await message.answer(f"❌ Minimum Withdraw ₹10\n\n💰 Your Balance: ₹{data[0] if data else 0}")
        return
    await WithdrawState.waiting_for_amount.set()
    await message.answer("💸 Enter Withdraw Amount")

@dp.message_handler(state=WithdrawState.waiting_for_amount)
async def save_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ Enter numbers only")
    amount = int(message.text)
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    bal = cursor.fetchone()[0]
    if amount < 10 or amount > bal:
        await message.answer(f"❌ Invalid Amount. Balance: ₹{bal}")
        return
    await state.update_data(amount=amount)
    await WithdrawState.waiting_for_upi.set()
    await message.answer("🏦 Send Your UPI ID")

@dp.message_handler(state=WithdrawState.waiting_for_upi)
async def save_upi(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (data['amount'], message.from_user.id))
    conn.commit()
    await bot.send_message(ADMIN_ID, f"💸 New Withdraw\n👤 @{message.from_user.username}\n💰 ₹{data['amount']}\n🏦 {message.text}")
    await message.answer("✅ Withdraw Request Sent")
    await state.finish()

@dp.message_handler(commands=['admin'])
async def admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        cursor.execute("SELECT COUNT(*) FROM users")
        await message.answer(f"👑 Total Users: {cursor.fetchone()[0]}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

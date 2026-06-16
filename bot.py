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
        [KeyboardButton(text="➜ 𝗣𝗹𝗮𝘆"), KeyboardButton(text="➜ 𝗥𝗲𝗳𝗳𝗲𝗿")],
        [KeyboardButton(text="➜ 𝗗𝗮𝗶𝗹𝘆 𝗕𝗼𝗻𝘂𝘀"), KeyboardButton(text="➜ 𝗧𝗮𝘀𝗸𝘀")],
        [KeyboardButton(text="➲ 𝐁𝐚𝐥𝐚𝐧𝐜𝐞")]
    ], resize_keyboard=True)

def balance_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Withdraw", callback_data="withdraw_action")]
    ])

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
        await call.message.answer("✅ Verification Successful!", reply_markup=main_menu())
    else:
        await call.answer("❌ Please join both channels first!", show_alert=True)

@dp.message(F.text == "➲ 𝐁𝐚𝐥𝐚𝐧𝐜𝐞")
async def balance(message: types.Message):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    res = cursor.fetchone()
    user_bal = res[0] if res else 0
    locked_bal = 500
    
    text = (
        f"📊 --- ACCOUNT SUMMARY ---\n\n"
        f"💰 Available Balance: ₹{user_bal}\n"
        f"🔒 Locked Balance: ₹{locked_bal}\n\n"
        f"🏧 Total Assets: ₹{user_bal + locked_bal}"
    )
    await message.answer(text, reply_markup=balance_menu())

@dp.callback_query(F.data == "withdraw_action")
async def withdraw_callback(call: CallbackQuery, state: FSMContext):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (call.from_user.id,))
    res = cursor.fetchone()
    if res and res[0] >= 10:
        await state.set_state(WithdrawState.waiting_for_amount)
        await call.message.answer("💸 Please enter the amount you want to withdraw:")
    else:
        await call.answer("❌ Minimum withdraw limit is ₹10", show_alert=True)

@dp.message(WithdrawState.waiting_for_amount)
async def get_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ Enter numeric value only.")
    await state.update_data(amount=message.text)
    await state.set_state(WithdrawState.waiting_for_upi)
    await message.answer("🏦 Send your UPI ID:")

@dp.message(WithdrawState.waiting_for_upi)
async def get_upi(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = int(data['amount'])
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, message.from_user.id))
    conn.commit()
    await bot.send_message(ADMIN_ID, f"💸 New Withdraw Request\nUser: {message.from_user.id}\nAmt: ₹{amount}\nUPI: {message.text}")
    await message.answer("✅ Request submitted to admin!")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import os
import sqlite3
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6897212040"))
PHOTO_URL = "https://i.postimg.cc/02GRzWDB/file-00000000d74071fa86d1d103d4ac7342.png"
CHANNELS = ["@Moneyearning_updates", "@bexamoneygroup"]

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)")
conn.commit()

# --- Keyboards ---
def main_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➜ Play"), KeyboardButton(text="➜ Reffer")],
        [KeyboardButton(text="➜ Daily Bonus"), KeyboardButton(text="➜ Tasks")],
        [KeyboardButton(text="➲ Balance"), KeyboardButton(text="📝 Task"), KeyboardButton(text="📊 Survey")],
        [KeyboardButton(text="🛍 Bexacart"), KeyboardButton(text="🎁 Rewards")]
    ], resize_keyboard=True)

# --- Handlers ---
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    ref_link = f"https://t.me/{(await bot.get_me()).username}?start={user_id}"
    caption = (f"✦ Welcome To {message.from_user.first_name} ✦\n\n"
               "❖ Complete Simple Task\n❖ Earn ₹250 Rewards\n❖ Join 2 Official Channels\n"
               "❖ Unlock Bot Access\n❖ Tap Verify After Joining\n\n"
               "Share your link & earn rewards on every purchase your friends make\n\n"
               f"➜ Share Link: {ref_link}")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➜ Join 1", url="https://t.me/Moneyearning_updates"),
         InlineKeyboardButton(text="➜ Join 2", url="https://t.me/bexamoneygroup")],
        [InlineKeyboardButton(text="➲ VERIFY", callback_data="verify")]
    ])
    await message.answer_photo(photo=PHOTO_URL, caption=caption, reply_markup=kb)

@dp.callback_query(F.data == "verify")
async def verify(call: CallbackQuery):
    await call.message.answer("✅ Verification Successful!", reply_markup=main_menu())

# Task Section (5 Buttons)
@dp.message(F.text == "📝 Task")
async def task_page(message: types.Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Watch Ads +20"), KeyboardButton(text="Join TG Channel +25")],
        [KeyboardButton(text="Follow Insta/Fb +20"), KeyboardButton(text="Subscribe YT +30")],
        [KeyboardButton(text="Rate Our App +50"), KeyboardButton(text="⬅️ Back")]
    ], resize_keyboard=True)
    await message.answer("Select Task:", reply_markup=kb)

# Survey Section (5 Buttons)
@dp.message(F.text == "📊 Survey")
async def survey_page(message: types.Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="1 Survay"), KeyboardButton(text="2 Survey")],
        [KeyboardButton(text="3 Survey"), KeyboardButton(text="4 Survey")],
        [KeyboardButton(text="5 Survey"), KeyboardButton(text="⬅️ Back")]
    ], resize_keyboard=True)
    await message.answer("Select Survey:", reply_markup=kb)

# Bexacart Section (5 Buttons)
@dp.message(F.text == "🛍 Bexacart")
async def shop_page(message: types.Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="1 Cloths"), KeyboardButton(text="2 Mobiles")],
        [KeyboardButton(text="3 Accessories"), KeyboardButton(text="4 Beauty")],
        [KeyboardButton(text="5 Others"), KeyboardButton(text="⬅️ Back")]
    ], resize_keyboard=True)
    await message.answer("Bexacart Deals:", reply_markup=kb)

# Rewards Section (5 Buttons)
@dp.message(F.text == "🎁 Rewards")
async def rewards_page(message: types.Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="1 My Vouchers"), KeyboardButton(text="2 Activate Double Points")],
        [KeyboardButton(text="3 Claim Reward"), KeyboardButton(text="4 Unlock Reward")],
        [KeyboardButton(text="5 View Rewards"), KeyboardButton(text="⬅️ Back")]
    ], resize_keyboard=True)
    await message.answer("Rewards:", reply_markup=kb)

@dp.message(F.text == "⬅️ Back")
async def back(message: types.Message):
    await message.answer("Back to Main:", reply_markup=main_menu())

# Balance & Withdraw
@dp.message(F.text == "➲ Balance")
async def balance_info(message: types.Message):
    text = "📊 --- ACCOUNT SUMMARY ---\n\n💰 Available Balance: ₹0\n🔒 Locked Balance: ₹500\n\n🏧 Total Assets: ₹500"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💳 Withdraw", callback_data="withdraw")]])
    await message.answer(text, reply_markup=kb)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
  

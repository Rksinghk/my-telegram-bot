import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Config
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6897212040"))
PHOTO_URL = "https://i.postimg.cc/02GRzWDB/file-00000000d74071fa86d1d103d4ac7342.png"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# DB Setup
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, refer_count INTEGER DEFAULT 0)")
conn.commit()

# --- Main Keyboards ---
def start_kb(user_id):
    ref_link = f"https://t.me/{(bot.get_me())}?start={user_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➜ Share Link", url=f"https://t.me/share/url?url={ref_link}")],
        [InlineKeyboardButton(text="➜ Join 1", url="https://t.me/Moneyearning_updates"), InlineKeyboardButton(text="➜ Join 2", url="https://t.me/bexamoneygroup")],
        [InlineKeyboardButton(text="➲ VERIFY", callback_data="verify")]
    ])

def menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➜ Task", callback_data="m_task"), InlineKeyboardButton(text="➜ Survey", callback_data="m_survey")],
        [InlineKeyboardButton(text="➜ Bexacart", callback_data="m_shop"), InlineKeyboardButton(text="➜ Rewards", callback_data="m_reward")],
        [InlineKeyboardButton(text="➲ Balance", callback_data="m_balance")]
    ])

# --- Handlers ---
@dp.message(Command("start"))
async def start(message: types.Message):
    caption = (f"✦ Welcome To {message.from_user.first_name} ✦\n\n"
               "❖ Complete Simple Task\n❖ Earn ₹250 Rewards\n❖ Join 2 Official Channels\n"
               "❖ Unlock Bot Access\n❖ Tap Verify After Joining\n\n"
               "Share your link & earn rewards on every purchase your friends make")
    await message.answer_photo(photo=PHOTO_URL, caption=caption, reply_markup=start_kb(message.from_user.id))

@dp.callback_query(F.data == "verify")
async def verify(call: CallbackQuery):
    await call.message.answer("✅ Verification Success! Choose an option:", reply_markup=menu_kb())

# --- Menu Logic (Nested Buttons) ---
@dp.callback_query(F.data == "m_task")
async def task_menu(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Watch Ads +20", callback_data="add_20")],
        [InlineKeyboardButton(text="Join TG Channel +25", callback_data="add_25")],
        [InlineKeyboardButton(text="Follow Insta/Fb +20", callback_data="add_20")],
        [InlineKeyboardButton(text="Subscribe YT +30", callback_data="add_30")],
        [InlineKeyboardButton(text="Rate Our App +50", callback_data="add_50")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
    ])
    await call.message.edit_text("📝 Select Task:", reply_markup=kb)

@dp.callback_query(F.data == "m_survey")
async def survey_menu(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 Survay", callback_data="s1"), InlineKeyboardButton(text="2 Survey", callback_data="s2")],
        [InlineKeyboardButton(text="3 Survey", callback_data="s3"), InlineKeyboardButton(text="4 Survey", callback_data="s4")],
        [InlineKeyboardButton(text="5 Survey", callback_data="s5")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
    ])
    await call.message.edit_text("📊 Select Survey:", reply_markup=kb)

@dp.callback_query(F.data == "m_shop")
async def shop_menu(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 Cloths", callback_data="shop1"), InlineKeyboardButton(text="2 Mobiles", callback_data="shop2")],
        [InlineKeyboardButton(text="3 Accessories", callback_data="shop3"), InlineKeyboardButton(text="4 Beauty", callback_data="shop4")],
        [InlineKeyboardButton(text="5 Others", callback_data="shop5")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
    ])
    await call.message.edit_text("🛍 Bexacart:", reply_markup=kb)

@dp.callback_query(F.data == "m_reward")
async def reward_menu(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 My Vouchers", callback_data="r1"), InlineKeyboardButton(text="2 Activate Double Points", callback_data="r2")],
        [InlineKeyboardButton(text="3 Claim Reward", callback_data="r3"), InlineKeyboardButton(text="4 Unlock Reward", callback_data="r4")],
        [InlineKeyboardButton(text="5 View Rewards", callback_data="r5")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
    ])
    await call.message.edit_text("🎁 Rewards:", reply_markup=kb)

@dp.callback_query(F.data == "m_balance")
async def balance_menu(call: CallbackQuery):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (call.from_user.id,))
    bal = cursor.fetchone()[0]
    text = f"📊 --- ACCOUNT SUMMARY ---\n\n💰 Available: ₹{bal}\n🔒 Locked: ₹500\n\n🏧 Total: ₹{bal + 500}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery):
    await call.message.edit_text("Choose an option:", reply_markup=menu_kb())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

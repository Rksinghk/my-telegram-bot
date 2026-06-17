import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Config
API_TOKEN = os.getenv("API_TOKEN")
CHANNELS = ["@Moneyearning_updates", "@bexamoneygroup"]
PHOTO_URL = "https://i.postimg.cc/02GRzWDB/file-00000000d74071fa86d1d103d4ac7342.png"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- Verification Check ---
async def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ['left', 'kicked']: return False
        except: return False
    return True

# --- Keyboards ---
def start_kb(user_id):
    ref_link = f"https://t.me/Real_Earnings_Bot?start={user_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➜ Share Link", url=f"https://t.me/share/url?url={ref_link}")],
        [InlineKeyboardButton(text="➜ Join 1", url="https://t.me/Moneyearning_updates"), InlineKeyboardButton(text="➜ Join 2", url="https://t.me/bexamoneygroup")],
        [InlineKeyboardButton(text="➲ VERIFY", callback_data="verify_user")]
    ])

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➜ Task", callback_data="m_task"), InlineKeyboardButton(text="➜ Survey", callback_data="m_survey")],
        [InlineKeyboardButton(text="➜ Bexacart", callback_data="m_shop"), InlineKeyboardButton(text="➜ Rewards", callback_data="m_reward")],
        [InlineKeyboardButton(text="➲ Balance", callback_data="m_balance")]
    ])

# --- Commands ---
@dp.message(Command("start"))
async def start(message: types.Message):
    caption = ("✦ Welcome To Bexa ✦\n\n"
               "❖ Complete Simple Task\n❖ Earn ₹250 Rewards\n❖ Join 2 Official Channels\n"
               "❖ Unlock Bot Access\n❖ Tap Verify After Joining\n\n"
               "Share your link & earn rewards on every purchase your friends make")
    await message.answer_photo(photo=PHOTO_URL, caption=caption, reply_markup=start_kb(message.from_user.id))

@dp.callback_query(F.data == "verify_user")
async def verify_user(call: CallbackQuery):
    if await check_subscription(call.from_user.id):
        await call.message.edit_caption(caption="✅ Verification Successful! Access Granted:", reply_markup=main_menu_kb())
    else:
        await call.answer("❌ Please join both channels first!", show_alert=True)

# --- Nested Logic ---
@dp.callback_query(F.data == "m_task")
async def task_menu(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Watch Ads +20 Coins", callback_data="c1")],
        [InlineKeyboardButton(text="Join TG Channel +25 Coins", callback_data="c2")],
        [InlineKeyboardButton(text="Follow Insta/Fb +20 Coins", callback_data="c3")],
        [InlineKeyboardButton(text="Subscribe YT +30 Coins", callback_data="c4")],
        [InlineKeyboardButton(text="Rate Our App +50 Coins", callback_data="c5")],
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
        [InlineKeyboardButton(text="1 Cloths", callback_data="sh1"), InlineKeyboardButton(text="2 Mobiles", callback_data="sh2")],
        [InlineKeyboardButton(text="3 Accessories", callback_data="sh3"), InlineKeyboardButton(text="4 Beauty", callback_data="sh4")],
        [InlineKeyboardButton(text="5 Others", callback_data="sh5")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
    ])
    await call.message.edit_text("🛍 Bexacart (Top Deals):", reply_markup=kb)

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
    text = "📊 --- ACCOUNT SUMMARY ---\n\n💰 Available Balance: ₹0\n🔒 Locked Balance: ₹500\n\n🏧 Total Assets: ₹500"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Withdraw", callback_data="withdraw_now")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "back_main")
async def back_to_menu(call: CallbackQuery):
    await call.message.edit_text("Menu:", reply_markup=main_menu_kb())

@dp.callback_query(F.data == "withdraw_now")
async def withdraw_process(call: CallbackQuery):
    await call.answer("💸 Request Sent to Admin!", show_alert=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

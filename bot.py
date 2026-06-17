"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TELEGRAM EARNING BOT
Built with Aiogram 3.20 | SQLite | Railway Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import asyncio
import logging
import os
import sqlite3
from datetime import datetime, date
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
    InputMediaPhoto, Message, URLInputFile
)

# ─── Load Env ───────────────────────────────────────────────────────────────
load_dotenv()

API_TOKEN    = os.getenv("API_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_ID     = int(os.getenv("ADMIN_ID", "123456789"))
BOT_USERNAME = os.getenv("BOT_USERNAME", "YourBot")

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# ─── Bot & Dispatcher ────────────────────────────────────────────────────────
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATABASE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DB_PATH = "earning_bot.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            full_name   TEXT,
            coins       INTEGER DEFAULT 0,
            locked_coins INTEGER DEFAULT 0,
            referrer_id INTEGER DEFAULT NULL,
            joined_at   TEXT DEFAULT CURRENT_TIMESTAMP,
            last_active TEXT DEFAULT CURRENT_TIMESTAMP,
            is_banned   INTEGER DEFAULT 0,
            is_verified INTEGER DEFAULT 0
        )
    """)

    # Task claims (once per day per task)
    c.execute("""
        CREATE TABLE IF NOT EXISTS task_claims (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            task_id     TEXT,
            claimed_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            coins_earned INTEGER
        )
    """)

    # Task opened tracking (must open before claim)
    c.execute("""
        CREATE TABLE IF NOT EXISTS task_opened (
            user_id  INTEGER,
            task_id  TEXT,
            opened_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, task_id)
        )
    """)

    # Withdraw requests
    c.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            coins       INTEGER,
            amount      REAL,
            method      TEXT,
            upi_id      TEXT,
            qr_file_id  TEXT,
            status      TEXT DEFAULT 'pending',
            requested_at TEXT DEFAULT CURRENT_TIMESTAMP,
            processed_at TEXT
        )
    """)

    # Settings table (key-value)
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Logs
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            action     TEXT,
            details    TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # ── Seed default settings ──
    defaults = {
        "welcome_message":  "✦ Welcome To {name} ✦\n\n❖ Complete Simple Task\n❖ Earn ₹250 Rewards\n❖ Join 2 Official Channels\n❖ Unlock Bot Access\n❖ Tap Verify After Joining\n\nShare your link & earn rewards on every purchase your friends make",
        "start_image":      "https://i.postimg.cc/02GRzWDB/file-00000000d74071fa86d1d103d4ac7342.png",
        "channel_1":        "https://t.me/Moneyearning_updates",
        "channel_1_id":     "@Moneyearning_updates",
        "channel_2":        "https://t.me/bexamoneygroup",
        "channel_2_id":     "@bexamoneygroup",
        "referral_bonus":   "100",
        "min_withdraw":     "500",
        # Task rewards (coins)
        "reward_watch_ads":      "20",
        "reward_join_tg":        "25",
        "reward_follow_insta":   "20",
        "reward_subscribe_yt":   "30",
        "reward_rate_app":       "50",
        "reward_survey_1":       "20",
        "reward_survey_2":       "25",
        "reward_survey_3":       "20",
        "reward_survey_4":       "30",
        "reward_survey_5":       "50",
        "reward_bexacart_1":     "20",
        "reward_bexacart_2":     "25",
        "reward_bexacart_3":     "20",
        "reward_bexacart_4":     "30",
        "reward_bexacart_5":     "50",
        "reward_rewards_1":      "20",
        "reward_rewards_2":      "25",
        "reward_rewards_3":      "20",
        "reward_rewards_4":      "30",
        "reward_rewards_5":      "50",
        # Task URLs (20 total)
        "url_watch_ads":         "https://example.com/ads",
        "url_join_tg":           "https://t.me/Moneyearning_updates",
        "url_follow_insta":      "https://instagram.com/",
        "url_subscribe_yt":      "https://youtube.com/",
        "url_rate_app":          "https://example.com/rate",
        "url_survey_1":          "https://example.com/survey1",
        "url_survey_2":          "https://example.com/survey2",
        "url_survey_3":          "https://example.com/survey3",
        "url_survey_4":          "https://example.com/survey4",
        "url_survey_5":          "https://example.com/survey5",
        "url_bexacart_1":        "https://bexacart.com/cloths",
        "url_bexacart_2":        "https://bexacart.com/mobiles",
        "url_bexacart_3":        "https://bexacart.com/accessories",
        "url_bexacart_4":        "https://bexacart.com/beauty",
        "url_bexacart_5":        "https://bexacart.com/others",
        "url_rewards_1":         "https://example.com/vouchers",
        "url_rewards_2":         "https://example.com/double",
        "url_rewards_3":         "https://example.com/claim",
        "url_rewards_4":         "https://example.com/unlock",
        "url_rewards_5":         "https://example.com/view",
        # Feature toggles
        "tasks_enabled":         "1",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()
    logger.info("Database initialized.")

def get_setting(key: str, default=None):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key: str, value: str):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def add_log(user_id, action, details=""):
    conn = get_db()
    conn.execute("INSERT INTO logs (user_id, action, details) VALUES (?, ?, ?)",
                 (user_id, action, details))
    conn.commit()
    conn.close()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# USER HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_user(user_id: int):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return user

def ensure_user(user_id: int, username: str, full_name: str, referrer_id: int = None):
    conn = get_db()
    existing = conn.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO users (user_id, username, full_name, referrer_id) VALUES (?, ?, ?, ?)",
            (user_id, username or "", full_name or "User", referrer_id)
        )
        conn.commit()
        is_new = True
    else:
        conn.execute(
            "UPDATE users SET username=?, full_name=?, last_active=CURRENT_TIMESTAMP WHERE user_id=?",
            (username or "", full_name or "User", user_id)
        )
        conn.commit()
        is_new = False
    conn.close()
    return is_new

def add_coins(user_id: int, coins: int):
    conn = get_db()
    conn.execute("UPDATE users SET coins = coins + ? WHERE user_id=?", (coins, user_id))
    conn.commit()
    conn.close()

def remove_coins(user_id: int, coins: int):
    conn = get_db()
    conn.execute("UPDATE users SET coins = MAX(0, coins - ?) WHERE user_id=?", (coins, user_id))
    conn.commit()
    conn.close()

def coins_to_rupees(coins: int) -> float:
    return round(coins / 40, 2)

def rupees_to_coins(rupees: float) -> int:
    return int(rupees * 40)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FSM STATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WithdrawStates(StatesGroup):
    choose_method = State()
    enter_upi     = State()
    upload_qr     = State()

class AdminStates(StatesGroup):
    broadcast          = State()
    ban_user           = State()
    unban_user         = State()
    add_coins          = State()
    remove_coins       = State()
    edit_welcome       = State()
    edit_start_image   = State()
    edit_channel_1     = State()
    edit_channel_2     = State()
    edit_referral_bonus = State()
    edit_min_withdraw  = State()
    edit_coin_reward   = State()  # stores which reward to edit in data
    edit_task_url      = State()  # stores which url to edit in data
    add_coins_amount   = State()
    remove_coins_amount = State()
    waiting_user_id    = State()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KEYBOARDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def kb_start():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➜ Share Link", callback_data="share_link")],
        [
            InlineKeyboardButton(text="➜ Join 1", url=get_setting("channel_1")),
            InlineKeyboardButton(text="➜ Join 2", url=get_setting("channel_2")),
        ],
        [InlineKeyboardButton(text="➲ VERIFY", callback_data="verify")],
    ])

def kb_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➜ Task",   callback_data="menu_task"),
            InlineKeyboardButton(text="➜ Survey", callback_data="menu_survey"),
        ],
        [
            InlineKeyboardButton(text="➜ Bexacart (Top Deals)", callback_data="menu_bexacart"),
            InlineKeyboardButton(text="➜ Rewards", callback_data="menu_rewards"),
        ],
        [InlineKeyboardButton(text="➲ Balance", callback_data="menu_balance")],
    ])

def kb_task_page():
    r = lambda k: get_setting(k, "0")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Watch Ads +{r('reward_watch_ads')} Coins",       callback_data="task_watch_ads")],
        [InlineKeyboardButton(text=f"Join TG Channel +{r('reward_join_tg')} Coins",   callback_data="task_join_tg")],
        [InlineKeyboardButton(text=f"Follow Insta/Facebook +{r('reward_follow_insta')} Coins", callback_data="task_follow_insta")],
        [InlineKeyboardButton(text=f"Subscribe YouTube +{r('reward_subscribe_yt')} Coins",    callback_data="task_subscribe_yt")],
        [InlineKeyboardButton(text=f"Rate Our App +{r('reward_rate_app')} Coins",     callback_data="task_rate_app")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_main")],
    ])

def kb_survey_page():
    r = lambda k: get_setting(k, "0")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"1 Survey +{r('reward_survey_1')} Coins",  callback_data="task_survey_1")],
        [InlineKeyboardButton(text=f"2 Survey +{r('reward_survey_2')} Coins",  callback_data="task_survey_2")],
        [InlineKeyboardButton(text=f"3 Survey +{r('reward_survey_3')} Coins",  callback_data="task_survey_3")],
        [InlineKeyboardButton(text=f"4 Survey +{r('reward_survey_4')} Coins",  callback_data="task_survey_4")],
        [InlineKeyboardButton(text=f"5 Survey +{r('reward_survey_5')} Coins",  callback_data="task_survey_5")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_main")],
    ])

def kb_bexacart_page():
    r = lambda k: get_setting(k, "0")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"1 Cloths +{r('reward_bexacart_1')} Coins",       callback_data="task_bexacart_1")],
        [InlineKeyboardButton(text=f"2 Mobiles +{r('reward_bexacart_2')} Coins",      callback_data="task_bexacart_2")],
        [InlineKeyboardButton(text=f"3 Accessories +{r('reward_bexacart_3')} Coins",  callback_data="task_bexacart_3")],
        [InlineKeyboardButton(text=f"4 Beauty +{r('reward_bexacart_4')} Coins",       callback_data="task_bexacart_4")],
        [InlineKeyboardButton(text=f"5 Others +{r('reward_bexacart_5')} Coins",       callback_data="task_bexacart_5")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_main")],
    ])

def kb_rewards_page():
    r = lambda k: get_setting(k, "0")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"1 My Vouchers +{r('reward_rewards_1')} Coins",         callback_data="task_rewards_1")],
        [InlineKeyboardButton(text=f"2 Activate Double Points +{r('reward_rewards_2')} Coins", callback_data="task_rewards_2")],
        [InlineKeyboardButton(text=f"3 Claim Reward +{r('reward_rewards_3')} Coins",        callback_data="task_rewards_3")],
        [InlineKeyboardButton(text=f"4 Unlock Reward +{r('reward_rewards_4')} Coins",       callback_data="task_rewards_4")],
        [InlineKeyboardButton(text=f"5 View Rewards +{r('reward_rewards_5')} Coins",        callback_data="task_rewards_5")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_main")],
    ])

def kb_task_action(task_id: str, url: str, coins: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Open Task", url=url, callback_data=f"open_{task_id}")],
        [InlineKeyboardButton(text=f"✅ Claim {coins} Coins", callback_data=f"claim_{task_id}")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_main")],
    ])

def kb_balance_page():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_main")],
    ])

def kb_withdraw_method():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 UPI ID",        callback_data="withdraw_upi")],
        [InlineKeyboardButton(text="📷 QR Screenshot", callback_data="withdraw_qr")],
        [InlineKeyboardButton(text="🔙 Cancel",        callback_data="back_main")],
    ])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CHANNEL MEMBERSHIP CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def check_membership(user_id: int) -> bool:
    ch1 = get_setting("channel_1_id", "@Moneyearning_updates")
    ch2 = get_setting("channel_2_id", "@bexamoneygroup")
    try:
        m1 = await bot.get_chat_member(ch1, user_id)
        m2 = await bot.get_chat_member(ch2, user_id)
        valid = ("member", "administrator", "creator")
        return m1.status in valid and m2.status in valid
    except Exception as e:
        logger.warning(f"Membership check failed: {e}")
        return False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TASK HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Mapping task_id → (reward_key, url_key, label)
TASK_META = {
    "watch_ads":    ("reward_watch_ads",    "url_watch_ads",    "Watch Ads",           "https://i.postimg.cc/3RxWHFPP/Untitled-June-18-2026-at-00-17-15-1-(2).png"),
    "join_tg":      ("reward_join_tg",      "url_join_tg",      "Join TG Channel",     "https://i.postimg.cc/3RxWHFPP/Untitled-June-18-2026-at-00-17-15-1-(2).png"),
    "follow_insta": ("reward_follow_insta", "url_follow_insta", "Follow Insta/Facebook","https://i.postimg.cc/3RxWHFPP/Untitled-June-18-2026-at-00-17-15-1-(2).png"),
    "subscribe_yt": ("reward_subscribe_yt", "url_subscribe_yt", "Subscribe YouTube",   "https://i.postimg.cc/3RxWHFPP/Untitled-June-18-2026-at-00-17-15-1-(2).png"),
    "rate_app":     ("reward_rate_app",     "url_rate_app",     "Rate Our App",        "https://i.postimg.cc/3RxWHFPP/Untitled-June-18-2026-at-00-17-15-1-(2).png"),
    "survey_1":     ("reward_survey_1",     "url_survey_1",     "Survey 1",            "https://i.postimg.cc/SKyxWGQv/Untitled-June-18-2026-at-00-17-15-2-(1).png"),
    "survey_2":     ("reward_survey_2",     "url_survey_2",     "Survey 2",            "https://i.postimg.cc/SKyxWGQv/Untitled-June-18-2026-at-00-17-15-2-(1).png"),
    "survey_3":     ("reward_survey_3",     "url_survey_3",     "Survey 3",            "https://i.postimg.cc/SKyxWGQv/Untitled-June-18-2026-at-00-17-15-2-(1).png"),
    "survey_4":     ("reward_survey_4",     "url_survey_4",     "Survey 4",            "https://i.postimg.cc/SKyxWGQv/Untitled-June-18-2026-at-00-17-15-2-(1).png"),
    "survey_5":     ("reward_survey_5",     "url_survey_5",     "Survey 5",            "https://i.postimg.cc/SKyxWGQv/Untitled-June-18-2026-at-00-17-15-2-(1).png"),
    "bexacart_1":   ("reward_bexacart_1",   "url_bexacart_1",   "Cloths",              "https://i.postimg.cc/Z0tT08D1/Untitled-June-18-2026-at-00-17-15-3-(1).png"),
    "bexacart_2":   ("reward_bexacart_2",   "url_bexacart_2",   "Mobiles",             "https://i.postimg.cc/Z0tT08D1/Untitled-June-18-2026-at-00-17-15-3-(1).png"),
    "bexacart_3":   ("reward_bexacart_3",   "url_bexacart_3",   "Accessories",         "https://i.postimg.cc/Z0tT08D1/Untitled-June-18-2026-at-00-17-15-3-(1).png"),
    "bexacart_4":   ("reward_bexacart_4",   "url_bexacart_4",   "Beauty",              "https://i.postimg.cc/Z0tT08D1/Untitled-June-18-2026-at-00-17-15-3-(1).png"),
    "bexacart_5":   ("reward_bexacart_5",   "url_bexacart_5",   "Others",              "https://i.postimg.cc/Z0tT08D1/Untitled-June-18-2026-at-00-17-15-3-(1).png"),
    "rewards_1":    ("reward_rewards_1",    "url_rewards_1",    "My Vouchers",         "https://i.postimg.cc/c4w3hXZH/Untitled-June-18-2026-at-00-17-15-4-(1).png"),
    "rewards_2":    ("reward_rewards_2",    "url_rewards_2",    "Activate Double Points","https://i.postimg.cc/c4w3hXZH/Untitled-June-18-2026-at-00-17-15-4-(1).png"),
    "rewards_3":    ("reward_rewards_3",    "url_rewards_3",    "Claim Reward",        "https://i.postimg.cc/c4w3hXZH/Untitled-June-18-2026-at-00-17-15-4-(1).png"),
    "rewards_4":    ("reward_rewards_4",    "url_rewards_4",    "Unlock Reward",       "https://i.postimg.cc/c4w3hXZH/Untitled-June-18-2026-at-00-17-15-4-(1).png"),
    "rewards_5":    ("reward_rewards_5",    "url_rewards_5",    "View Rewards",        "https://i.postimg.cc/c4w3hXZH/Untitled-June-18-2026-at-00-17-15-4-(1).png"),
}

def has_opened_task(user_id: int, task_id: str) -> bool:
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM task_opened WHERE user_id=? AND task_id=?",
        (user_id, task_id)
    ).fetchone()
    conn.close()
    return row is not None

def mark_task_opened(user_id: int, task_id: str):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO task_opened (user_id, task_id, opened_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (user_id, task_id)
    )
    conn.commit()
    conn.close()

def claimed_today(user_id: int, task_id: str) -> bool:
    today = date.today().isoformat()
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM task_claims WHERE user_id=? AND task_id=? AND DATE(claimed_at)=?",
        (user_id, task_id, today)
    ).fetchone()
    conn.close()
    return row is not None

def record_claim(user_id: int, task_id: str, coins: int):
    conn = get_db()
    conn.execute(
        "INSERT INTO task_claims (user_id, task_id, coins_earned) VALUES (?, ?, ?)",
        (user_id, task_id, coins)
    )
    conn.commit()
    conn.close()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# /start HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    args = message.text.split()
    referrer_id = None

    if len(args) > 1:
        try:
            referrer_id = int(args[1])
            if referrer_id == user.id:
                referrer_id = None
        except ValueError:
            pass

    is_new = ensure_user(user.id, user.username, user.full_name, referrer_id)

    db_user = get_user(user.id)
    if db_user and db_user["is_banned"]:
        await message.answer("🚫 You are banned from using this bot.")
        return

    # Give referral bonus if new user with valid referrer
    if is_new and referrer_id:
        referrer = get_user(referrer_id)
        if referrer:
            bonus = int(get_setting("referral_bonus", "100"))
            add_coins(referrer_id, bonus)
            add_log(referrer_id, "referral_bonus", f"Referred {user.id}, +{bonus} coins")
            try:
                await bot.send_message(
                    referrer_id,
                    f"🎉 <b>New Referral!</b>\n{user.full_name} joined via your link.\n+{bonus} coins added to your account!"
                )
            except Exception:
                pass

    welcome = get_setting("welcome_message", "Welcome!").replace("{name}", user.full_name)
    image_url = get_setting("start_image")

    await message.answer_photo(
        photo=image_url,
        caption=welcome,
        reply_markup=kb_start()
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECRET ADMIN COMMAND
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.message(Command("admin_2905"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return  # Silently ignore

    conn = get_db()
    total_users    = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    today_str      = date.today().isoformat()
    active_today   = conn.execute(
        "SELECT COUNT(*) as c FROM users WHERE DATE(last_active)=?", (today_str,)
    ).fetchone()["c"]
    total_refs     = conn.execute(
        "SELECT COUNT(*) as c FROM users WHERE referrer_id IS NOT NULL"
    ).fetchone()["c"]
    total_coins    = conn.execute("SELECT SUM(coins_earned) as c FROM task_claims").fetchone()["c"] or 0
    pending_w      = conn.execute(
        "SELECT COUNT(*) as c FROM withdrawals WHERE status='pending'"
    ).fetchone()["c"]
    conn.close()

    text = (
        "🔐 <b>Admin Panel</b>\n\n"
        f"👥 Total Users: <b>{total_users}</b>\n"
        f"🟢 Active Today: <b>{active_today}</b>\n"
        f"👥 Total Referrals: <b>{total_refs}</b>\n"
        f"🪙 Total Coins Distributed: <b>{total_coins}</b>\n"
        f"💳 Pending Withdrawals: <b>{pending_w}</b>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Broadcast",     callback_data="adm_broadcast"),
            InlineKeyboardButton(text="🚫 Ban User",       callback_data="adm_ban"),
        ],
        [
            InlineKeyboardButton(text="✅ Unban User",    callback_data="adm_unban"),
            InlineKeyboardButton(text="💰 Add Coins",      callback_data="adm_add_coins"),
        ],
        [
            InlineKeyboardButton(text="➖ Remove Coins",  callback_data="adm_remove_coins"),
            InlineKeyboardButton(text="💳 Withdrawals",   callback_data="adm_withdrawals"),
        ],
        [
            InlineKeyboardButton(text="📝 Edit Welcome",  callback_data="adm_edit_welcome"),
            InlineKeyboardButton(text="🖼 Edit Image",    callback_data="adm_edit_image"),
        ],
        [
            InlineKeyboardButton(text="📢 Edit Channel 1", callback_data="adm_edit_ch1"),
            InlineKeyboardButton(text="📢 Edit Channel 2", callback_data="adm_edit_ch2"),
        ],
        [
            InlineKeyboardButton(text="🎁 Referral Bonus",  callback_data="adm_edit_ref_bonus"),
            InlineKeyboardButton(text="💰 Min Withdraw",    callback_data="adm_edit_min_w"),
        ],
        [
            InlineKeyboardButton(text="🪙 Edit Rewards",    callback_data="adm_edit_rewards"),
            InlineKeyboardButton(text="🔗 Edit Task URLs",  callback_data="adm_edit_urls"),
        ],
        [
            InlineKeyboardButton(text="🟢 Toggle Tasks",    callback_data="adm_toggle_tasks"),
            InlineKeyboardButton(text="📊 Logs",            callback_data="adm_logs"),
        ],
    ])
    await message.answer(text, reply_markup=kb)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VERIFY CALLBACK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.callback_query(F.data == "verify")
async def cb_verify(call: CallbackQuery):
    user = call.from_user
    db_user = get_user(user.id)
    if not db_user:
        ensure_user(user.id, user.username, user.full_name)

    is_member = await check_membership(user.id)
    if not is_member:
        await call.answer(
            "❌ Please join BOTH channels first, then tap Verify!",
            show_alert=True
        )
        return

    # Mark as verified
    conn = get_db()
    conn.execute("UPDATE users SET is_verified=1 WHERE user_id=?", (user.id,))
    conn.commit()
    conn.close()

    await call.answer("✅ Verified! Welcome!", show_alert=True)
    await call.message.answer(
        f"✅ <b>Access Unlocked!</b>\n\nWelcome, {user.full_name}!\nUse the menu below to start earning.",
        reply_markup=kb_main_menu()
    )
    add_log(user.id, "verified", "User verified channel membership")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SHARE LINK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.callback_query(F.data == "share_link")
async def cb_share_link(call: CallbackQuery):
    user = call.from_user
    link = f"https://t.me/{BOT_USERNAME}?start={user.id}"
    bonus = get_setting("referral_bonus", "100")
    await call.message.answer(
        f"🔗 <b>Your Referral Link:</b>\n<code>{link}</code>\n\n"
        f"🎁 Earn <b>{bonus} coins</b> for every friend who joins!\n\n"
        f"Share this link and grow your earnings!"
    )
    await call.answer()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VERIFIED GUARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def guard_verified(call: CallbackQuery) -> bool:
    db_user = get_user(call.from_user.id)
    if not db_user or not db_user["is_verified"]:
        await call.answer("⚠️ Please verify channel membership first!", show_alert=True)
        return False
    if db_user["is_banned"]:
        await call.answer("🚫 You are banned.", show_alert=True)
        return False
    return True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN MENU CALLBACKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.callback_query(F.data == "back_main")
async def cb_back_main(call: CallbackQuery):
    if not await guard_verified(call):
        return
    await call.message.answer("📋 <b>Main Menu</b>", reply_markup=kb_main_menu())
    await call.answer()

@router.callback_query(F.data == "menu_task")
async def cb_menu_task(call: CallbackQuery):
    if not await guard_verified(call):
        return
    if get_setting("tasks_enabled", "1") == "0":
        await call.answer("⚠️ Tasks are currently disabled.", show_alert=True)
        return
    await call.message.answer_photo(
        photo="https://i.postimg.cc/3RxWHFPP/Untitled-June-18-2026-at-00-17-15-1-(2).png",
        caption="📋 <b>Task Page</b>\nComplete tasks and earn coins!",
        reply_markup=kb_task_page()
    )
    await call.answer()

@router.callback_query(F.data == "menu_survey")
async def cb_menu_survey(call: CallbackQuery):
    if not await guard_verified(call):
        return
    await call.message.answer_photo(
        photo="https://i.postimg.cc/SKyxWGQv/Untitled-June-18-2026-at-00-17-15-2-(1).png",
        caption="📝 <b>Survey Page</b>\nComplete surveys and earn coins!",
        reply_markup=kb_survey_page()
    )
    await call.answer()

@router.callback_query(F.data == "menu_bexacart")
async def cb_menu_bexacart(call: CallbackQuery):
    if not await guard_verified(call):
        return
    await call.message.answer_photo(
        photo="https://i.postimg.cc/Z0tT08D1/Untitled-June-18-2026-at-00-17-15-3-(1).png",
        caption="🛒 <b>Bexacart - Top Deals</b>\nShop and earn coins!",
        reply_markup=kb_bexacart_page()
    )
    await call.answer()

@router.callback_query(F.data == "menu_rewards")
async def cb_menu_rewards(call: CallbackQuery):
    if not await guard_verified(call):
        return
    await call.message.answer_photo(
        photo="https://i.postimg.cc/c4w3hXZH/Untitled-June-18-2026-at-00-17-15-4-(1).png",
        caption="🎁 <b>Rewards Page</b>\nUnlock and claim rewards!",
        reply_markup=kb_rewards_page()
    )
    await call.answer()

@router.callback_query(F.data == "menu_balance")
async def cb_menu_balance(call: CallbackQuery):
    if not await guard_verified(call):
        return
    user = get_user(call.from_user.id)
    coins    = user["coins"]
    locked   = user["locked_coins"]
    balance  = coins_to_rupees(coins)
    locked_r = coins_to_rupees(locked)
    total    = round(balance + locked_r, 2)
    await call.message.answer(
        f"💼 <b>Your Balance</b>\n\n"
        f"🪙 Coins: <b>{coins}</b>\n"
        f"💰 Available Balance: <b>₹{balance}</b>\n"
        f"🔒 Locked Balance: <b>₹{locked_r}</b>\n"
        f"🏧 Total Assets: <b>₹{total}</b>\n\n"
        f"<i>40 Coins = ₹1</i>",
        reply_markup=kb_balance_page()
    )
    await call.answer()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TASK BUTTON HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.callback_query(F.data.startswith("task_"))
async def cb_task_button(call: CallbackQuery):
    if not await guard_verified(call):
        return

    task_id = call.data[5:]  # strip "task_"
    if task_id not in TASK_META:
        await call.answer("Unknown task.", show_alert=True)
        return

    reward_key, url_key, label, img_url = TASK_META[task_id]
    coins = int(get_setting(reward_key, "0"))
    url   = get_setting(url_key, "https://t.me/")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Open Task", url=url)],
        [InlineKeyboardButton(text=f"✅ Claim {coins} Coins", callback_data=f"claim_{task_id}")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_main")],
    ])

    await call.message.answer_photo(
        photo=img_url,
        caption=(
            f"📌 <b>{label}</b>\n\n"
            f"1️⃣ Click <b>Open Task</b>\n"
            f"2️⃣ Complete the task\n"
            f"3️⃣ Come back & click <b>Claim {coins} Coins</b>\n\n"
            f"⚠️ You must open the task before claiming!"
        ),
        reply_markup=kb
    )
    # Mark as opened when user sees this page
    mark_task_opened(call.from_user.id, task_id)
    await call.answer()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLAIM HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.callback_query(F.data.startswith("claim_"))
async def cb_claim(call: CallbackQuery):
    if not await guard_verified(call):
        return

    task_id = call.data[6:]  # strip "claim_"
    user_id = call.from_user.id

    if task_id not in TASK_META:
        await call.answer("Unknown task.", show_alert=True)
        return

    # Must have opened task first
    if not has_opened_task(user_id, task_id):
        await call.answer("⚠️ Please open the task first before claiming!", show_alert=True)
        return

    # Check daily limit
    if claimed_today(user_id, task_id):
        await call.answer("⚠️ Today's reward already claimed. Come back tomorrow!", show_alert=True)
        return

    reward_key = TASK_META[task_id][0]
    label      = TASK_META[task_id][2]
    coins = int(get_setting(reward_key, "0"))

    add_coins(user_id, coins)
    record_claim(user_id, task_id, coins)
    add_log(user_id, "task_claim", f"task={task_id}, coins={coins}")

    await call.answer(f"✅ +{coins} Coins added!", show_alert=True)
    await call.message.answer(
        f"🎉 <b>Coins Claimed!</b>\n\n"
        f"📌 Task: <b>{label}</b>\n"
        f"🪙 +<b>{coins} Coins</b> added to your account!\n\n"
        f"Total balance updated. Use /start to see your balance."
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WITHDRAW FLOW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.callback_query(F.data == "withdraw")
async def cb_withdraw(call: CallbackQuery, state: FSMContext):
    if not await guard_verified(call):
        return

    user = get_user(call.from_user.id)
    coins = user["coins"]
    min_w = int(get_setting("min_withdraw", "500"))
    min_coins = rupees_to_coins(min_w)

    if coins < min_coins:
        await call.answer(
            f"❌ Minimum withdrawal is ₹{min_w} ({min_coins} coins).\nYou have {coins} coins.",
            show_alert=True
        )
        return

    await call.message.answer(
        f"💳 <b>Withdraw</b>\n\n"
        f"🪙 Your Coins: <b>{coins}</b>\n"
        f"💰 Amount: <b>₹{coins_to_rupees(coins)}</b>\n\n"
        f"Choose withdrawal method:",
        reply_markup=kb_withdraw_method()
    )
    await state.set_state(WithdrawStates.choose_method)
    await call.answer()

@router.callback_query(F.data == "withdraw_upi", WithdrawStates.choose_method)
async def cb_withdraw_upi(call: CallbackQuery, state: FSMContext):
    await state.set_state(WithdrawStates.enter_upi)
    await call.message.answer("💳 Please enter your <b>UPI ID</b>:")
    await call.answer()

@router.message(WithdrawStates.enter_upi)
async def process_upi(message: Message, state: FSMContext):
    upi = message.text.strip()
    user_id = message.from_user.id
    user = get_user(user_id)
    coins = user["coins"]
    amount = coins_to_rupees(coins)
    min_w = int(get_setting("min_withdraw", "500"))

    if coins < rupees_to_coins(min_w):
        await message.answer("❌ Insufficient coins for withdrawal.")
        await state.clear()
        return

    # Save withdrawal
    conn = get_db()
    conn.execute(
        "INSERT INTO withdrawals (user_id, coins, amount, method, upi_id) VALUES (?, ?, ?, 'upi', ?)",
        (user_id, coins, amount, upi)
    )
    w_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
    conn.commit()
    conn.close()

    add_log(user_id, "withdraw_request", f"method=UPI, amount=₹{amount}, upi={upi}")

    # Notify admin
    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"wadm_approve_{w_id}"),
            InlineKeyboardButton(text="❌ Reject",  callback_data=f"wadm_reject_{w_id}"),
        ]
    ])
    await bot.send_message(
        ADMIN_ID,
        f"💳 <b>Withdrawal Request #{w_id}</b>\n\n"
        f"👤 Name: {user['full_name']}\n"
        f"🆔 User ID: {user_id}\n"
        f"🪙 Coins: {coins}\n"
        f"💰 Amount: ₹{amount}\n"
        f"💳 UPI: <code>{upi}</code>",
        reply_markup=kb_admin
    )

    await message.answer(
        f"✅ <b>Withdrawal Request Sent!</b>\n\n"
        f"💰 Amount: ₹{amount}\n"
        f"💳 UPI: {upi}\n\n"
        f"Admin will process it soon."
    )
    await state.clear()

@router.callback_query(F.data == "withdraw_qr", WithdrawStates.choose_method)
async def cb_withdraw_qr(call: CallbackQuery, state: FSMContext):
    await state.set_state(WithdrawStates.upload_qr)
    await call.message.answer("📷 Please send your <b>QR Code screenshot</b>:")
    await call.answer()

@router.message(WithdrawStates.upload_qr, F.photo)
async def process_qr(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = get_user(user_id)
    coins = user["coins"]
    amount = coins_to_rupees(coins)
    qr_id = message.photo[-1].file_id

    conn = get_db()
    conn.execute(
        "INSERT INTO withdrawals (user_id, coins, amount, method, qr_file_id) VALUES (?, ?, ?, 'qr', ?)",
        (user_id, coins, amount, qr_id)
    )
    w_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
    conn.commit()
    conn.close()

    add_log(user_id, "withdraw_request", f"method=QR, amount=₹{amount}")

    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"wadm_approve_{w_id}"),
            InlineKeyboardButton(text="❌ Reject",  callback_data=f"wadm_reject_{w_id}"),
        ]
    ])
    await bot.send_photo(
        ADMIN_ID,
        photo=qr_id,
        caption=(
            f"💳 <b>Withdrawal Request #{w_id}</b>\n\n"
            f"👤 Name: {user['full_name']}\n"
            f"🆔 User ID: {user_id}\n"
            f"🪙 Coins: {coins}\n"
            f"💰 Amount: ₹{amount}\n"
            f"📷 Method: QR"
        ),
        reply_markup=kb_admin
    )
    await message.answer(
        f"✅ <b>Withdrawal Request Sent!</b>\n\n"
        f"💰 Amount: ₹{amount}\n"
        f"📷 Method: QR Code\n\n"
        f"Admin will process it soon."
    )
    await state.clear()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADMIN — WITHDRAWAL APPROVE/REJECT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.callback_query(F.data.startswith("wadm_"))
async def cb_wadm(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return

    parts  = call.data.split("_")
    action = parts[1]  # approve / reject
    w_id   = int(parts[2])

    conn = get_db()
    w = conn.execute("SELECT * FROM withdrawals WHERE id=?", (w_id,)).fetchone()

    if not w:
        await call.answer("Withdrawal not found.", show_alert=True)
        conn.close()
        return

    if w["status"] != "pending":
        await call.answer(f"Already {w['status']}.", show_alert=True)
        conn.close()
        return

    if action == "approve":
        # Deduct coins
        conn.execute("UPDATE users SET coins = MAX(0, coins - ?) WHERE user_id=?",
                     (w["coins"], w["user_id"]))
        conn.execute(
            "UPDATE withdrawals SET status='approved', processed_at=CURRENT_TIMESTAMP WHERE id=?",
            (w_id,)
        )
        conn.commit()
        conn.close()
        add_log(w["user_id"], "withdraw_approved", f"₹{w['amount']}")
        await call.answer("✅ Approved!", show_alert=True)
        await call.message.edit_caption(call.message.caption + "\n\n✅ <b>APPROVED</b>")
        try:
            await bot.send_message(
                w["user_id"],
                f"✅ <b>Withdrawal Approved!</b>\n💰 ₹{w['amount']} has been processed.\nCoins deducted from your account."
            )
        except Exception:
            pass

    elif action == "reject":
        conn.execute(
            "UPDATE withdrawals SET status='rejected', processed_at=CURRENT_TIMESTAMP WHERE id=?",
            (w_id,)
        )
        conn.commit()
        conn.close()
        add_log(w["user_id"], "withdraw_rejected", f"₹{w['amount']}")
        await call.answer("❌ Rejected!", show_alert=True)
        await call.message.edit_caption(call.message.caption + "\n\n❌ <b>REJECTED</b>")
        try:
            await bot.send_message(
                w["user_id"],
                f"❌ <b>Withdrawal Rejected!</b>\n\nYour request for ₹{w['amount']} was rejected by admin.\nCoins have NOT been deducted."
            )
        except Exception:
            pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADMIN PANEL CALLBACKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def is_admin(call: CallbackQuery) -> bool:
    return call.from_user.id == ADMIN_ID

# ── Broadcast ──
@router.callback_query(F.data == "adm_broadcast")
async def adm_broadcast(call: CallbackQuery, state: FSMContext):
    if not is_admin(call): return
    await state.set_state(AdminStates.broadcast)
    await call.message.answer("📢 Send the broadcast message (text/photo/video):")
    await call.answer()

@router.message(AdminStates.broadcast)
async def do_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return

    conn = get_db()
    users = conn.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()
    conn.close()

    sent = failed = 0
    for u in users:
        try:
            await message.copy_to(u["user_id"])
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await message.answer(f"📢 Broadcast complete!\n✅ Sent: {sent}\n❌ Failed: {failed}")
    await state.clear()

# ── Ban ──
@router.callback_query(F.data == "adm_ban")
async def adm_ban(call: CallbackQuery, state: FSMContext):
    if not is_admin(call): return
    await state.set_state(AdminStates.ban_user)
    await call.message.answer("🚫 Enter User ID to ban:")
    await call.answer()

@router.message(AdminStates.ban_user)
async def do_ban(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    try:
        uid = int(message.text.strip())
        conn = get_db()
        conn.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        add_log(uid, "banned", f"by admin")
        await message.answer(f"✅ User {uid} banned.")
    except ValueError:
        await message.answer("❌ Invalid user ID.")
    await state.clear()

# ── Unban ──
@router.callback_query(F.data == "adm_unban")
async def adm_unban(call: CallbackQuery, state: FSMContext):
    if not is_admin(call): return
    await state.set_state(AdminStates.unban_user)
    await call.message.answer("✅ Enter User ID to unban:")
    await call.answer()

@router.message(AdminStates.unban_user)
async def do_unban(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    try:
        uid = int(message.text.strip())
        conn = get_db()
        conn.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        await message.answer(f"✅ User {uid} unbanned.")
    except ValueError:
        await message.answer("❌ Invalid user ID.")
    await state.clear()

# ── Add Coins ──
@router.callback_query(F.data == "adm_add_coins")
async def adm_add_coins(call: CallbackQuery, state: FSMContext):
    if not is_admin(call): return
    await state.set_state(AdminStates.waiting_user_id)
    await state.update_data(next_action="add_coins")
    await call.message.answer("💰 Enter User ID:")
    await call.answer()

@router.callback_query(F.data == "adm_remove_coins")
async def adm_remove_coins(call: CallbackQuery, state: FSMContext):
    if not is_admin(call): return
    await state.set_state(AdminStates.waiting_user_id)
    await state.update_data(next_action="remove_coins")
    await call.message.answer("➖ Enter User ID:")
    await call.answer()

@router.message(AdminStates.waiting_user_id)
async def adm_get_uid(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    try:
        uid = int(message.text.strip())
        data = await state.get_data()
        await state.update_data(target_uid=uid)
        action = data.get("next_action")
        if action == "add_coins":
            await state.set_state(AdminStates.add_coins_amount)
            await message.answer(f"💰 How many coins to ADD to user {uid}?")
        else:
            await state.set_state(AdminStates.remove_coins_amount)
            await message.answer(f"➖ How many coins to REMOVE from user {uid}?")
    except ValueError:
        await message.answer("❌ Invalid ID.")
        await state.clear()

@router.message(AdminStates.add_coins_amount)
async def do_add_coins(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    data = await state.get_data()
    uid = data.get("target_uid")
    try:
        coins = int(message.text.strip())
        add_coins(uid, coins)
        add_log(uid, "admin_add_coins", f"+{coins}")
        await message.answer(f"✅ Added {coins} coins to user {uid}.")
    except ValueError:
        await message.answer("❌ Invalid amount.")
    await state.clear()

@router.message(AdminStates.remove_coins_amount)
async def do_remove_coins(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    data = await state.get_data()
    uid = data.get("target_uid")
    try:
        coins = int(message.text.strip())
        remove_coins(uid, coins)
        add_log(uid, "admin_remove_coins", f"-{coins}")
        await message.answer(f"✅ Removed {coins} coins from user {uid}.")
    except ValueError:
        await message.answer("❌ Invalid amount.")
    await state.clear()

# ── Pending Withdrawals ──
@router.callback_query(F.data == "adm_withdrawals")
async def adm_withdrawals(call: CallbackQuery):
    if not is_admin(call): return
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM withdrawals WHERE status='pending' ORDER BY requested_at DESC LIMIT 10"
    ).fetchall()
    conn.close()
    if not rows:
        await call.message.answer("✅ No pending withdrawals.")
        await call.answer()
        return
    for w in rows:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Approve", callback_data=f"wadm_approve_{w['id']}"),
            InlineKeyboardButton(text="❌ Reject",  callback_data=f"wadm_reject_{w['id']}"),
        ]])
        user = get_user(w["user_id"])
        name = user["full_name"] if user else "Unknown"
        text = (
            f"💳 <b>Request #{w['id']}</b>\n"
            f"👤 {name} ({w['user_id']})\n"
            f"🪙 {w['coins']} coins → ₹{w['amount']}\n"
            f"💳 Method: {w['method']}\n"
            f"📅 {w['requested_at']}"
        )
        if w["method"] == "qr" and w["qr_file_id"]:
            await call.message.answer_photo(photo=w["qr_file_id"], caption=text, reply_markup=kb)
        else:
            if w["upi_id"]:
                text += f"\n💳 UPI: <code>{w['upi_id']}</code>"
            await call.message.answer(text, reply_markup=kb)
    await call.answer()

# ── Edit Welcome ──
@router.callback_query(F.data == "adm_edit_welcome")
async def adm_edit_welcome(call: CallbackQuery, state: FSMContext):
    if not is_admin(call): return
    current = get_setting("welcome_message")
    await state.set_state(AdminStates.edit_welcome)
    await call.message.answer(
        f"📝 Current welcome message:\n\n<code>{current}</code>\n\nSend new welcome message:\n(Use {{name}} for user's name)"
    )
    await call.answer()

@router.message(AdminStates.edit_welcome)
async def do_edit_welcome(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    set_setting("welcome_message", message.text)
    await message.answer("✅ Welcome message updated.")
    await state.clear()

# ── Edit Start Image ──
@router.callback_query(F.data == "adm_edit_image")
async def adm_edit_image(call: CallbackQuery, state: FSMContext):
    if not is_admin(call): return
    await state.set_state(AdminStates.edit_start_image)
    await call.message.answer("🖼 Send new start image URL:")
    await call.answer()

@router.message(AdminStates.edit_start_image)
async def do_edit_image(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    set_setting("start_image", message.text.strip())
    await message.answer("✅ Start image updated.")
    await state.clear()

# ── Edit Channel 1 ──
@router.callback_query(F.data == "adm_edit_ch1")
async def adm_edit_ch1(call: CallbackQuery, state: FSMContext):
    if not is_admin(call): return
    await state.set_state(AdminStates.edit_channel_1)
    await call.message.answer(
        f"📢 Current Channel 1: {get_setting('channel_1')}\n\n"
        "Send new channel link (e.g. https://t.me/channel) and channel_id (e.g. @channel) separated by newline:"
    )
    await call.answer()

@router.message(AdminStates.edit_channel_1)
async def do_edit_ch1(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    parts = message.text.strip().split("\n")
    if len(parts) >= 2:
        set_setting("channel_1", parts[0].strip())
        set_setting("channel_1_id", parts[1].strip())
        await message.answer("✅ Channel 1 updated.")
    else:
        await message.answer("❌ Send both link and @username on separate lines.")
    await state.clear()

# ── Edit Channel 2 ──
@router.callback_query(F.data == "adm_edit_ch2")
async def adm_edit_ch2(call: CallbackQuery, state: FSMContext):
    if not is_admin(call): return
    await state.set_state(AdminStates.edit_channel_2)
    await call.message.answer(
        f"📢 Current Channel 2: {get_setting('channel_2')}\n\n"
        "Send new channel link and @username on separate lines:"
    )
    await call.answer()

@router.message(AdminStates.edit_channel_2)
async def do_edit_ch2(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    parts = message.text.strip().split("\n")
    if len(parts) >= 2:
        set_setting("channel_2", parts[0].strip())
        set_setting("channel_2_id", parts[1].strip())
        await message.answer("✅ Channel 2 updated.")
    else:
        await message.answer("❌ Send both link and @username on separate lines.")
    await state.clear()

# ── Edit Referral Bonus ──
@router.callback_query(F.data == "adm_edit_ref_bonus")
async def adm_edit_ref_bonus(call: CallbackQuery, state: FSMContext):
    if not is_admin(call): return
    await state.set_state(AdminStates.edit_referral_bonus)
    await call.message.answer(f"🎁 Current referral bonus: {get_setting('referral_bonus')} coins\n\nEnter new value:")
    await call.answer()

@router.message(AdminStates.edit_referral_bonus)
async def do_edit_ref_bonus(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    try:
        val = int(message.text.strip())
        set_setting("referral_bonus", str(val))
        await message.answer(f"✅ Referral bonus set to {val} coins.")
    except ValueError:
        await message.answer("❌ Enter a valid number.")
    await state.clear()

# ── Edit Min Withdraw ──
@router.callback_query(F.data == "adm_edit_min_w")
async def adm_edit_min_w(call: CallbackQuery, state: FSMContext):
    if not is_admin(call): return
    await state.set_state(AdminStates.edit_min_withdraw)
    await call.message.answer(f"💰 Current min withdraw: ₹{get_setting('min_withdraw')}\n\nEnter new value (in ₹):")
    await call.answer()

@router.message(AdminStates.edit_min_withdraw)
async def do_edit_min_w(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    try:
        val = int(message.text.strip())
        set_setting("min_withdraw", str(val))
        await message.answer(f"✅ Minimum withdrawal set to ₹{val}.")
    except ValueError:
        await message.answer("❌ Enter a valid number.")
    await state.clear()

# ── Edit Coin Rewards ──
@router.callback_query(F.data == "adm_edit_rewards")
async def adm_edit_rewards(call: CallbackQuery):
    if not is_admin(call): return
    all_rewards = [k for k in [
        "reward_watch_ads","reward_join_tg","reward_follow_insta","reward_subscribe_yt","reward_rate_app",
        "reward_survey_1","reward_survey_2","reward_survey_3","reward_survey_4","reward_survey_5",
        "reward_bexacart_1","reward_bexacart_2","reward_bexacart_3","reward_bexacart_4","reward_bexacart_5",
        "reward_rewards_1","reward_rewards_2","reward_rewards_3","reward_rewards_4","reward_rewards_5",
    ]]
    buttons = []
    for r in all_rewards:
        label = r.replace("reward_", "").replace("_", " ").title()
        val = get_setting(r, "0")
        buttons.append([InlineKeyboardButton(text=f"{label}: {val}", callback_data=f"editr_{r}")])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="adm_back")])
    await call.message.answer("🪙 Select reward to edit:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await call.answer()

@router.callback_query(F.data.startswith("editr_"))
async def adm_editr_select(call: CallbackQuery, state: FSMContext):
    if not is_admin(call): return
    key = call.data[6:]
    await state.set_state(AdminStates.edit_coin_reward)
    await state.update_data(reward_key=key)
    label = key.replace("reward_", "").replace("_", " ").title()
    await call.message.answer(f"🪙 Enter new coin reward for <b>{label}</b>:")
    await call.answer()

@router.message(AdminStates.edit_coin_reward)
async def do_edit_coin_reward(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    data = await state.get_data()
    key  = data.get("reward_key")
    try:
        val = int(message.text.strip())
        set_setting(key, str(val))
        await message.answer(f"✅ Reward updated to {val} coins.")
    except ValueError:
        await message.answer("❌ Enter a valid number.")
    await state.clear()

# ── Edit Task URLs ──
@router.callback_query(F.data == "adm_edit_urls")
async def adm_edit_urls(call: CallbackQuery):
    if not is_admin(call): return
    all_urls = [
        "url_watch_ads","url_join_tg","url_follow_insta","url_subscribe_yt","url_rate_app",
        "url_survey_1","url_survey_2","url_survey_3","url_survey_4","url_survey_5",
        "url_bexacart_1","url_bexacart_2","url_bexacart_3","url_bexacart_4","url_bexacart_5",
        "url_rewards_1","url_rewards_2","url_rewards_3","url_rewards_4","url_rewards_5",
    ]
    buttons = []
    for u in all_urls:
        label = u.replace("url_", "").replace("_", " ").title()
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"editurl_{u}")])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="adm_back")])
    await call.message.answer("🔗 Select task URL to edit:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await call.answer()

@router.callback_query(F.data.startswith("editurl_"))
async def adm_editurl_select(call: CallbackQuery, state: FSMContext):
    if not is_admin(call): return
    key = call.data[8:]
    await state.set_state(AdminStates.edit_task_url)
    await state.update_data(url_key=key)
    label = key.replace("url_", "").replace("_", " ").title()
    current = get_setting(key, "")
    await call.message.answer(
        f"🔗 Current URL for <b>{label}</b>:\n<code>{current}</code>\n\nEnter new URL:"
    )
    await call.answer()

@router.message(AdminStates.edit_task_url)
async def do_edit_task_url(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    data = await state.get_data()
    key  = data.get("url_key")
    url  = message.text.strip()
    set_setting(key, url)
    await message.answer("✅ URL updated.")
    await state.clear()

# ── Toggle Tasks ──
@router.callback_query(F.data == "adm_toggle_tasks")
async def adm_toggle_tasks(call: CallbackQuery):
    if not is_admin(call): return
    current = get_setting("tasks_enabled", "1")
    new_val = "0" if current == "1" else "1"
    set_setting("tasks_enabled", new_val)
    status = "Enabled ✅" if new_val == "1" else "Disabled ❌"
    await call.answer(f"Tasks {status}", show_alert=True)

# ── Logs ──
@router.callback_query(F.data == "adm_logs")
async def adm_logs(call: CallbackQuery):
    if not is_admin(call): return
    conn = get_db()
    rows = conn.execute("SELECT * FROM logs ORDER BY created_at DESC LIMIT 20").fetchall()
    conn.close()
    if not rows:
        await call.message.answer("📊 No logs yet.")
        await call.answer()
        return
    text = "📊 <b>Recent Logs (last 20)</b>\n\n"
    for r in rows:
        text += f"• [{r['created_at'][:16]}] <b>{r['action']}</b> | UID:{r['user_id']} | {r['details']}\n"
    await call.message.answer(text[:4096])
    await call.answer()

@router.callback_query(F.data == "adm_back")
async def adm_back(call: CallbackQuery):
    if not is_admin(call): return
    await call.answer()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STARTUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def main():
    init_db()
    logger.info("Bot starting...")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())

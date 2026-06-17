# =============================================================================
# TELEGRAM EARNING BOT — Bot.py
# Framework : Aiogram 3.20
# Database  : SQLite (aiosqlite)
# Deploy    : Railway + GitHub (single-file)
# =============================================================================

import asyncio
import logging
import os
import sqlite3
import time
from datetime import datetime, date
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from dotenv import load_dotenv

# ─── Load environment ────────────────────────────────────────────────────────
load_dotenv()
API_TOKEN    = os.getenv("API_TOKEN", "")
ADMIN_ID     = int(os.getenv("ADMIN_ID", "0"))
BOT_USERNAME = os.getenv("BOT_USERNAME", "myearningbot")

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Bot / Dispatcher ─────────────────────────────────────────────────────────
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp  = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# =============================================================================
# DATABASE LAYER
# =============================================================================

DB_FILE = "earning_bot.db"


def get_db():
    """Return a synchronous SQLite connection (used only at startup for schema)."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables and seed default settings if they don't exist."""
    conn = get_db()
    c = conn.cursor()

    # ── Users ──────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id      INTEGER PRIMARY KEY,
            username     TEXT,
            full_name    TEXT,
            referred_by  INTEGER DEFAULT 0,
            coins        INTEGER DEFAULT 0,
            locked_coins INTEGER DEFAULT 0,
            joined_at    TEXT DEFAULT CURRENT_TIMESTAMP,
            is_banned    INTEGER DEFAULT 0,
            last_active  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Daily reward tracker ───────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_rewards (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER,
            action    TEXT,
            reward_date TEXT,
            UNIQUE(user_id, action, reward_date)
        )
    """)

    # ── Withdrawals ────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER,
            coins        INTEGER,
            method       TEXT,       -- 'upi' or 'qr'
            detail       TEXT,       -- UPI ID or file_id of QR screenshot
            status       TEXT DEFAULT 'pending',
            requested_at TEXT DEFAULT CURRENT_TIMESTAMP,
            processed_at TEXT
        )
    """)

    # ── Settings (key-value) ───────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # ── Activity log ──────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            action     TEXT,
            detail     TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # ── Seed default settings ──────────────────────────────────────────────
    defaults = {
        # welcome
        "welcome_caption": (
            "✦ Welcome To {name} ✦\n\n"
            "❖ Complete Simple Task\n"
            "❖ Earn ₹250 Rewards\n"
            "❖ Join 2 Official Channels\n"
            "❖ Unlock Bot Access\n"
            "❖ Tap Verify After Joining\n\n"
            "Share your link & earn rewards on every purchase your friends make"
        ),
        "start_image": "",          # file_id; empty = no image
        # force-join channels  (format: @channelusername|https://t.me/...)
        "channel_1": "@yourchannel1|https://t.me/yourchannel1",
        "channel_2": "@yourchannel2|https://t.me/yourchannel2",
        # coins
        "referral_bonus":    "50",
        "coins_per_rupee":   "40",    # 1000 coins = ₹25 → 40 coins/₹
        "min_withdraw_coins":"1000",
        # ─── Task rewards ──────────────────────────────────────────────
        "reward_watch_ads":        "20",
        "reward_join_tg":          "25",
        "reward_follow_social":    "20",
        "reward_subscribe_yt":     "30",
        "reward_rate_app":         "50",
        # ─── Survey rewards ────────────────────────────────────────────
        "reward_survey_1": "20",
        "reward_survey_2": "25",
        "reward_survey_3": "20",
        "reward_survey_4": "30",
        "reward_survey_5": "50",
        # ─── Bexacart rewards ──────────────────────────────────────────
        "reward_bexacart_1": "20",
        "reward_bexacart_2": "25",
        "reward_bexacart_3": "20",
        "reward_bexacart_4": "30",
        "reward_bexacart_5": "50",
        # ─── Rewards section rewards ───────────────────────────────────
        "reward_vouchers":       "20",
        "reward_double_points":  "25",
        "reward_claim":          "20",
        "reward_unlock":         "30",
        "reward_view":           "50",
        # ─── Links (Task) ──────────────────────────────────────────────
        "link_watch_ads":      "https://example.com/ads",
        "link_join_tg":        "https://t.me/joinchat/example",
        "link_follow_social":  "https://instagram.com/example",
        "link_subscribe_yt":   "https://youtube.com/example",
        "link_rate_app":       "https://play.google.com/store/apps/example",
        # ─── Links (Survey) ────────────────────────────────────────────
        "link_survey_1": "https://example.com/survey1",
        "link_survey_2": "https://example.com/survey2",
        "link_survey_3": "https://example.com/survey3",
        "link_survey_4": "https://example.com/survey4",
        "link_survey_5": "https://example.com/survey5",
        # ─── Links (Bexacart) ──────────────────────────────────────────
        "link_bexacart_1": "https://bexacart.com/cloths",
        "link_bexacart_2": "https://bexacart.com/mobiles",
        "link_bexacart_3": "https://bexacart.com/accessories",
        "link_bexacart_4": "https://bexacart.com/beauty",
        "link_bexacart_5": "https://bexacart.com/others",
        # ─── Links (Rewards section) ───────────────────────────────────
        "link_vouchers":      "https://example.com/vouchers",
        "link_double_points": "https://example.com/double",
        "link_claim":         "https://example.com/claim",
        "link_unlock":        "https://example.com/unlock",
        "link_view_rewards":  "https://example.com/view",
    }

    for key, value in defaults.items():
        c.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )

    conn.commit()
    conn.close()
    logger.info("Database initialised.")


# ─── Sync helpers (called in async context via run_in_executor) ───────────────

def _get_setting(key: str) -> str:
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else ""


def _set_setting(key: str, value: str):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
    )
    conn.commit()
    conn.close()


def _get_user(user_id: int) -> Optional[sqlite3.Row]:
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row


def _upsert_user(user_id: int, username: str, full_name: str, referred_by: int = 0):
    conn = get_db()
    conn.execute(
        """
        INSERT INTO users (user_id, username, full_name, referred_by)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username    = excluded.username,
            full_name   = excluded.full_name,
            last_active = CURRENT_TIMESTAMP
        """,
        (user_id, username, full_name, referred_by),
    )
    conn.commit()
    conn.close()


def _add_coins(user_id: int, coins: int):
    conn = get_db()
    conn.execute(
        "UPDATE users SET coins = coins + ? WHERE user_id = ?", (coins, user_id)
    )
    conn.commit()
    conn.close()


def _deduct_coins(user_id: int, coins: int):
    conn = get_db()
    conn.execute(
        "UPDATE users SET coins = MAX(0, coins - ?) WHERE user_id = ?",
        (coins, user_id),
    )
    conn.commit()
    conn.close()


def _check_daily(user_id: int, action: str) -> bool:
    """Return True if the user has NOT yet claimed this reward today."""
    today = date.today().isoformat()
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM daily_rewards WHERE user_id=? AND action=? AND reward_date=?",
        (user_id, action, today),
    ).fetchone()
    conn.close()
    return row is None


def _mark_daily(user_id: int, action: str):
    today = date.today().isoformat()
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO daily_rewards (user_id, action, reward_date) VALUES (?,?,?)",
            (user_id, action, today),
        )
        conn.commit()
    finally:
        conn.close()


def _log(user_id: int, action: str, detail: str = ""):
    conn = get_db()
    conn.execute(
        "INSERT INTO logs (user_id, action, detail) VALUES (?,?,?)",
        (user_id, action, detail),
    )
    conn.commit()
    conn.close()


def _create_withdrawal(user_id: int, coins: int, method: str, detail: str) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO withdrawals (user_id, coins, method, detail) VALUES (?,?,?,?)",
        (user_id, coins, method, detail),
    )
    wid = cur.lastrowid
    conn.commit()
    conn.close()
    return wid


def _get_withdrawal(wid: int) -> Optional[sqlite3.Row]:
    conn = get_db()
    row = conn.execute("SELECT * FROM withdrawals WHERE id=?", (wid,)).fetchone()
    conn.close()
    return row


def _update_withdrawal_status(wid: int, status: str):
    conn = get_db()
    conn.execute(
        "UPDATE withdrawals SET status=?, processed_at=CURRENT_TIMESTAMP WHERE id=?",
        (status, wid),
    )
    conn.commit()
    conn.close()


def _stats():
    conn = get_db()
    total   = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    active  = conn.execute(
        "SELECT COUNT(*) FROM users WHERE date(last_active) = date('now')"
    ).fetchone()[0]
    pending = conn.execute(
        "SELECT COUNT(*) FROM withdrawals WHERE status='pending'"
    ).fetchone()[0]
    banned  = conn.execute("SELECT COUNT(*) FROM users WHERE is_banned=1").fetchone()[0]
    conn.close()
    return total, active, pending, banned


# Async wrappers using asyncio.get_event_loop().run_in_executor
async def setting(key: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_setting, key)


async def set_setting(key: str, value: str):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _set_setting, key, value)


async def get_user(user_id: int):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_user, user_id)


async def upsert_user(user_id, username, full_name, referred_by=0):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _upsert_user, user_id, username, full_name, referred_by)


async def add_coins(user_id, coins):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _add_coins, user_id, coins)


async def deduct_coins(user_id, coins):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _deduct_coins, user_id, coins)


async def check_daily(user_id, action) -> bool:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _check_daily, user_id, action)


async def mark_daily(user_id, action):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _mark_daily, user_id, action)


async def log(user_id, action, detail=""):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _log, user_id, action, detail)


async def create_withdrawal(user_id, coins, method, detail) -> int:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _create_withdrawal, user_id, coins, method, detail)


async def get_withdrawal(wid):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_withdrawal, wid)


async def update_withdrawal_status(wid, status):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _update_withdrawal_status, wid, status)


async def stats():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _stats)


# =============================================================================
# FSM STATES
# =============================================================================

class WithdrawStates(StatesGroup):
    choosing_method = State()
    entering_upi    = State()
    uploading_qr    = State()


class AdminStates(StatesGroup):
    broadcast           = State()
    ban_user            = State()
    unban_user          = State()
    edit_welcome        = State()
    edit_image          = State()
    edit_channel_1      = State()
    edit_channel_2      = State()
    edit_referral_bonus = State()
    edit_min_withdraw   = State()
    edit_coin_reward    = State()   # generic; context stored in FSM data
    edit_link           = State()   # generic; key stored in FSM data


# =============================================================================
# KEYBOARDS
# =============================================================================

def kb_start(channel_1_url: str, channel_2_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➜ Share Link",   callback_data="share_link"),
        ],
        [
            InlineKeyboardButton(text="➜ Join 1", url=channel_1_url),
            InlineKeyboardButton(text="➜ Join 2", url=channel_2_url),
        ],
        [
            InlineKeyboardButton(text="➲ VERIFY", callback_data="verify"),
        ],
    ])


def kb_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➜ Task"),    KeyboardButton(text="➜ Survey")],
            [KeyboardButton(text="➜ Bexacart (Top Deals)"), KeyboardButton(text="➜ Rewards")],
            [KeyboardButton(text="➲ Balance")],
        ],
        resize_keyboard=True,
    )


def kb_task(links: dict, rewards: dict) -> InlineKeyboardMarkup:
    """5 task buttons, each opens a link; coins awarded on tap (once/day)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"📺 Watch Ads +{rewards['watch_ads']} Coins",
            url=links["watch_ads"],
        )],
        [InlineKeyboardButton(
            text=f"📢 Join TG Channel +{rewards['join_tg']} Coins",
            url=links["join_tg"],
        )],
        [InlineKeyboardButton(
            text=f"📸 Follow Insta/Facebook +{rewards['follow_social']} Coins",
            url=links["follow_social"],
        )],
        [InlineKeyboardButton(
            text=f"▶️ Subscribe YouTube +{rewards['subscribe_yt']} Coins",
            url=links["subscribe_yt"],
        )],
        [InlineKeyboardButton(
            text=f"⭐ Rate Our App +{rewards['rate_app']} Coins",
            url=links["rate_app"],
        )],
        [InlineKeyboardButton(text="↩ Back", callback_data="back_main")],
    ])


def kb_task_claim(rewards: dict) -> InlineKeyboardMarkup:
    """Separate claim buttons so Aiogram can award coins on callback."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ Claim Watch Ads (+{rewards['watch_ads']})",       callback_data="claim_watch_ads")],
        [InlineKeyboardButton(text=f"✅ Claim Join TG (+{rewards['join_tg']})",           callback_data="claim_join_tg")],
        [InlineKeyboardButton(text=f"✅ Claim Follow Social (+{rewards['follow_social']})", callback_data="claim_follow_social")],
        [InlineKeyboardButton(text=f"✅ Claim Subscribe YT (+{rewards['subscribe_yt']})", callback_data="claim_subscribe_yt")],
        [InlineKeyboardButton(text=f"✅ Claim Rate App (+{rewards['rate_app']})",         callback_data="claim_rate_app")],
        [InlineKeyboardButton(text="↩ Back", callback_data="back_main")],
    ])


def _generic_menu(items, cb_prefix, back_cb="back_main") -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=label, callback_data=f"{cb_prefix}_{key}")]
            for key, label in items]
    rows.append([InlineKeyboardButton(text="↩ Back", callback_data=back_cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_survey(links: dict, rewards: dict) -> InlineKeyboardMarkup:
    items = [(str(i), f"📝 Survey {i} +{rewards[str(i)]} Coins") for i in range(1, 6)]
    rows = []
    for key, label in items:
        rows.append([InlineKeyboardButton(text=label, url=links[key])])
    rows.append([InlineKeyboardButton(text="↩ Back", callback_data="back_main")])
    # Also add claim row
    for i in range(1, 6):
        rows.insert(i * 2 - 1, [InlineKeyboardButton(
            text=f"✅ Claim Survey {i}", callback_data=f"claim_survey_{i}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_bexacart(links: dict, rewards: dict) -> InlineKeyboardMarkup:
    names = {1: "Cloths", 2: "Mobiles", 3: "Accessories", 4: "Beauty", 5: "Others"}
    rows = []
    for i in range(1, 6):
        rows.append([InlineKeyboardButton(
            text=f"🛒 {names[i]} +{rewards[str(i)]} Coins", url=links[str(i)]
        )])
        rows.append([InlineKeyboardButton(
            text=f"✅ Claim {names[i]}", callback_data=f"claim_bexacart_{i}"
        )])
    rows.append([InlineKeyboardButton(text="↩ Back", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_rewards_section(links: dict, rewards: dict) -> InlineKeyboardMarkup:
    names = {
        "vouchers": "🎟 My Vouchers",
        "double_points": "💥 Activate Double Points",
        "claim": "🎁 Claim Reward",
        "unlock": "🔓 Unlock Reward",
        "view": "👀 View Rewards",
    }
    rows = []
    for key, label in names.items():
        rows.append([InlineKeyboardButton(
            text=f"{label} +{rewards[key]} Coins", url=links[key]
        )])
        rows.append([InlineKeyboardButton(
            text=f"✅ Claim {label.split(' ', 1)[1]}", callback_data=f"claim_rewards_{key}"
        )])
    rows.append([InlineKeyboardButton(text="↩ Back", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_balance(coins: int, locked: int) -> InlineKeyboardMarkup:
    rate = 40  # 1000 coins = ₹25 → 40 coins/₹
    available_rupees = coins / rate if rate else 0
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"💰 Coins: {coins}  |  ₹{available_rupees:.2f}",
            callback_data="noop"
        )],
        [InlineKeyboardButton(
            text=f"🔒 Locked: {locked} Coins",
            callback_data="noop"
        )],
        [InlineKeyboardButton(
            text=f"📊 Total Assets: {coins + locked} Coins",
            callback_data="noop"
        )],
        [InlineKeyboardButton(text="💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton(text="↩ Back",      callback_data="back_main")],
    ])


def kb_withdraw_method() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏦 UPI ID",          callback_data="withdraw_upi")],
        [InlineKeyboardButton(text="📸 QR Screenshot",   callback_data="withdraw_qr")],
        [InlineKeyboardButton(text="❌ Cancel",           callback_data="back_main")],
    ])


def kb_admin_panel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Dashboard",           callback_data="adm_dashboard")],
        [InlineKeyboardButton(text="📣 Broadcast",           callback_data="adm_broadcast")],
        [InlineKeyboardButton(text="🚫 Ban User",            callback_data="adm_ban"),
         InlineKeyboardButton(text="✅ Unban User",          callback_data="adm_unban")],
        [InlineKeyboardButton(text="✏️ Welcome Message",     callback_data="adm_edit_welcome")],
        [InlineKeyboardButton(text="🖼 Start Image",         callback_data="adm_edit_image")],
        [InlineKeyboardButton(text="📢 Channel Links",       callback_data="adm_edit_channels")],
        [InlineKeyboardButton(text="💰 Referral Bonus",      callback_data="adm_edit_ref_bonus")],
        [InlineKeyboardButton(text="💵 Min Withdraw",        callback_data="adm_edit_min_withdraw")],
        [InlineKeyboardButton(text="🪙 Coin Rewards",        callback_data="adm_edit_rewards")],
        [InlineKeyboardButton(text="🔗 Edit All 20 Links",   callback_data="adm_edit_links")],
        [InlineKeyboardButton(text="📋 Logs",                callback_data="adm_logs")],
        [InlineKeyboardButton(text="⏳ Pending Withdrawals", callback_data="adm_pending_wd")],
    ])


def kb_admin_rewards() -> InlineKeyboardMarkup:
    """Sub-menu to pick which reward to edit."""
    keys = [
        ("reward_watch_ads",    "Watch Ads"),
        ("reward_join_tg",      "Join TG"),
        ("reward_follow_social","Follow Social"),
        ("reward_subscribe_yt", "Subscribe YT"),
        ("reward_rate_app",     "Rate App"),
        ("reward_survey_1",     "Survey 1"),
        ("reward_survey_2",     "Survey 2"),
        ("reward_survey_3",     "Survey 3"),
        ("reward_survey_4",     "Survey 4"),
        ("reward_survey_5",     "Survey 5"),
        ("reward_bexacart_1",   "Bexacart Cloths"),
        ("reward_bexacart_2",   "Bexacart Mobiles"),
        ("reward_bexacart_3",   "Bexacart Access."),
        ("reward_bexacart_4",   "Bexacart Beauty"),
        ("reward_bexacart_5",   "Bexacart Others"),
        ("reward_vouchers",     "Reward Vouchers"),
        ("reward_double_points","Double Points"),
        ("reward_claim",        "Claim Reward"),
        ("reward_unlock",       "Unlock Reward"),
        ("reward_view",         "View Rewards"),
    ]
    rows = [[InlineKeyboardButton(text=label, callback_data=f"adm_reward_{key}")]
            for key, label in keys]
    rows.append([InlineKeyboardButton(text="↩ Back", callback_data="adm_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_admin_links() -> InlineKeyboardMarkup:
    keys = [
        ("link_watch_ads",      "Watch Ads"),
        ("link_join_tg",        "Join TG"),
        ("link_follow_social",  "Follow Social"),
        ("link_subscribe_yt",   "Subscribe YT"),
        ("link_rate_app",       "Rate App"),
        ("link_survey_1",       "Survey 1"),
        ("link_survey_2",       "Survey 2"),
        ("link_survey_3",       "Survey 3"),
        ("link_survey_4",       "Survey 4"),
        ("link_survey_5",       "Survey 5"),
        ("link_bexacart_1",     "Bexacart Cloths"),
        ("link_bexacart_2",     "Bexacart Mobiles"),
        ("link_bexacart_3",     "Bexacart Access."),
        ("link_bexacart_4",     "Bexacart Beauty"),
        ("link_bexacart_5",     "Bexacart Others"),
        ("link_vouchers",       "Vouchers"),
        ("link_double_points",  "Double Points"),
        ("link_claim",          "Claim Reward"),
        ("link_unlock",         "Unlock Reward"),
        ("link_view_rewards",   "View Rewards"),
    ]
    rows = [[InlineKeyboardButton(text=label, callback_data=f"adm_link_{key}")]
            for key, label in keys]
    rows.append([InlineKeyboardButton(text="↩ Back", callback_data="adm_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_approve_reject(wid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"wd_approve_{wid}"),
            InlineKeyboardButton(text="❌ Reject",  callback_data=f"wd_reject_{wid}"),
        ]
    ])


# =============================================================================
# HELPERS
# =============================================================================

async def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


async def check_banned(user_id: int) -> bool:
    user = await get_user(user_id)
    return bool(user and user["is_banned"])


async def check_membership(user_id: int) -> bool:
    """Return True if the user is a member of both force-join channels."""
    ch1_raw = await setting("channel_1")
    ch2_raw = await setting("channel_2")

    async def member(ch_raw):
        ch_username = ch_raw.split("|")[0].strip()
        try:
            member = await bot.get_chat_member(ch_username, user_id)
            return member.status not in ("left", "kicked", "banned")
        except Exception as e:
            logger.warning(f"Membership check error for {ch_username}: {e}")
            return False

    r1 = await member(ch1_raw)
    r2 = await member(ch2_raw)
    return r1 and r2


async def send_start_screen(user_id: int, name: str, referred_by: int = 0):
    """Send the start / welcome screen to a user."""
    caption_tpl = await setting("welcome_caption")
    caption = caption_tpl.replace("{name}", name)
    caption += f"\n\n🔗 Your Referral Link:\n<code>https://t.me/{BOT_USERNAME}?start={user_id}</code>"

    ch1_raw = await setting("channel_1")
    ch2_raw = await setting("channel_2")
    ch1_url = ch1_raw.split("|")[-1].strip()
    ch2_url = ch2_raw.split("|")[-1].strip()

    image_id = await setting("start_image")
    markup = kb_start(ch1_url, ch2_url)

    if image_id:
        await bot.send_photo(user_id, photo=image_id, caption=caption, reply_markup=markup)
    else:
        await bot.send_message(user_id, caption, reply_markup=markup)


async def coins_to_rupees(coins: int) -> str:
    rate_str = await setting("coins_per_rupee")
    rate = float(rate_str) if rate_str else 40.0
    return f"₹{coins / rate:.2f}"


# =============================================================================
# COMMAND HANDLERS
# =============================================================================

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    args = message.text.split(maxsplit=1)
    referred_by = 0

    if len(args) > 1:
        try:
            referred_by = int(args[1])
            if referred_by == user.id:
                referred_by = 0
        except ValueError:
            referred_by = 0

    # Upsert user
    await upsert_user(user.id, user.username or "", user.full_name, referred_by)

    # Award referral bonus to referrer (only if new user)
    existing = await get_user(user.id)
    if referred_by and existing and existing["coins"] == 0:
        bonus_str = await setting("referral_bonus")
        bonus = int(bonus_str) if bonus_str.isdigit() else 50
        await add_coins(referred_by, bonus)
        await log(referred_by, "referral_bonus", f"Referred user {user.id}, +{bonus} coins")
        try:
            await bot.send_message(
                referred_by,
                f"🎉 <b>Referral Bonus!</b>\nYour friend <b>{user.full_name}</b> joined.\n"
                f"You earned <b>{bonus} Coins</b>!",
            )
        except Exception:
            pass

    if await check_banned(user.id):
        await message.answer("🚫 You have been banned from this bot.")
        return

    await send_start_screen(user.id, user.full_name, referred_by)
    await log(user.id, "start", f"ref={referred_by}")


@router.message(Command("admin_2905"))
async def cmd_admin(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return
    await message.answer("🛡 <b>Admin Panel</b>", reply_markup=kb_admin_panel())


# =============================================================================
# MAIN MENU — Reply keyboard
# =============================================================================

@router.message(F.text == "➜ Task")
async def menu_task(message: Message):
    if await check_banned(message.from_user.id):
        return
    # Load links & rewards from DB
    links = {
        "watch_ads":     await setting("link_watch_ads"),
        "join_tg":       await setting("link_join_tg"),
        "follow_social": await setting("link_follow_social"),
        "subscribe_yt":  await setting("link_subscribe_yt"),
        "rate_app":      await setting("link_rate_app"),
    }
    rewards = {
        "watch_ads":     await setting("reward_watch_ads"),
        "join_tg":       await setting("reward_join_tg"),
        "follow_social": await setting("reward_follow_social"),
        "subscribe_yt":  await setting("reward_subscribe_yt"),
        "rate_app":      await setting("reward_rate_app"),
    }
    await message.answer(
        "📋 <b>Task Menu</b>\nComplete tasks to earn coins.\n"
        "👆 Open the link, then tap ✅ Claim to get your coins (once/day).",
        reply_markup=kb_task(links, rewards),
    )
    # Also send claim buttons
    await message.answer("👇 Tap to claim your daily reward:", reply_markup=kb_task_claim(rewards))


@router.message(F.text == "➜ Survey")
async def menu_survey(message: Message):
    if await check_banned(message.from_user.id):
        return
    links = {str(i): await setting(f"link_survey_{i}") for i in range(1, 6)}
    rewards = {str(i): await setting(f"reward_survey_{i}") for i in range(1, 6)}
    await message.answer("📝 <b>Survey Menu</b>\nComplete surveys to earn coins (once/day each).",
                         reply_markup=kb_survey(links, rewards))


@router.message(F.text == "➜ Bexacart (Top Deals)")
async def menu_bexacart(message: Message):
    if await check_banned(message.from_user.id):
        return
    links = {str(i): await setting(f"link_bexacart_{i}") for i in range(1, 6)}
    rewards = {str(i): await setting(f"reward_bexacart_{i}") for i in range(1, 6)}
    await message.answer("🛒 <b>Bexacart — Top Deals</b>\nShop & earn coins (once/day each category).",
                         reply_markup=kb_bexacart(links, rewards))


@router.message(F.text == "➜ Rewards")
async def menu_rewards(message: Message):
    if await check_banned(message.from_user.id):
        return
    links = {
        "vouchers":      await setting("link_vouchers"),
        "double_points": await setting("link_double_points"),
        "claim":         await setting("link_claim"),
        "unlock":        await setting("link_unlock"),
        "view":          await setting("link_view_rewards"),
    }
    rewards = {
        "vouchers":      await setting("reward_vouchers"),
        "double_points": await setting("reward_double_points"),
        "claim":         await setting("reward_claim"),
        "unlock":        await setting("reward_unlock"),
        "view":          await setting("reward_view"),
    }
    await message.answer("🎁 <b>Rewards</b>\nUnlock great rewards (once/day each).",
                         reply_markup=kb_rewards_section(links, rewards))


@router.message(F.text == "➲ Balance")
async def menu_balance(message: Message):
    if await check_banned(message.from_user.id):
        return
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Please /start first.")
        return
    coins  = user["coins"]
    locked = user["locked_coins"]
    rate_str = await setting("coins_per_rupee")
    rate = float(rate_str) if rate_str else 40.0
    txt = (
        f"💰 <b>Your Balance</b>\n\n"
        f"🪙 Coins : <b>{coins}</b>  ({coins/rate:.2f} ₹)\n"
        f"🔒 Locked: <b>{locked}</b> ({locked/rate:.2f} ₹)\n"
        f"📊 Total : <b>{coins+locked}</b> ({(coins+locked)/rate:.2f} ₹)\n\n"
        f"<i>1000 Coins = ₹25</i>"
    )
    await message.answer(txt, reply_markup=kb_balance(coins, locked))


# =============================================================================
# CALLBACK HANDLERS
# =============================================================================

# ── Verify (force-join check) ─────────────────────────────────────────────────
@router.callback_query(F.data == "verify")
async def cb_verify(cq: CallbackQuery):
    await cq.answer()
    if await check_banned(cq.from_user.id):
        await cq.message.answer("🚫 You are banned.")
        return
    joined = await check_membership(cq.from_user.id)
    if joined:
        await cq.message.answer(
            "✅ <b>Verified!</b> Welcome aboard.",
            reply_markup=kb_main_menu(),
        )
    else:
        ch1_raw = await setting("channel_1")
        ch2_raw = await setting("channel_2")
        ch1_url = ch1_raw.split("|")[-1].strip()
        ch2_url = ch2_raw.split("|")[-1].strip()
        await cq.message.answer(
            "⚠️ You haven't joined both channels yet.\n"
            "Please join both and then tap <b>VERIFY</b> again.",
            reply_markup=kb_start(ch1_url, ch2_url),
        )


# ── Share link ────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "share_link")
async def cb_share_link(cq: CallbackQuery):
    await cq.answer()
    uid = cq.from_user.id
    link = f"https://t.me/{BOT_USERNAME}?start={uid}"
    await cq.message.answer(
        f"🔗 <b>Your Referral Link</b>\n\n<code>{link}</code>\n\n"
        "Share this link with friends and earn a bonus for every friend who joins!"
    )


# ── Back to main ──────────────────────────────────────────────────────────────
@router.callback_query(F.data == "back_main")
async def cb_back_main(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    await state.clear()
    await cq.message.answer("🏠 Main Menu", reply_markup=kb_main_menu())


# ── noop ──────────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "noop")
async def cb_noop(cq: CallbackQuery):
    await cq.answer()


# ── Generic daily-reward claim ────────────────────────────────────────────────
async def _handle_claim(cq: CallbackQuery, action: str, reward_key: str, label: str):
    """Unified claim logic: check daily, award coins, respond."""
    await cq.answer()
    uid = cq.from_user.id
    if await check_banned(uid):
        await cq.message.answer("🚫 You are banned.")
        return
    can_claim = await check_daily(uid, action)
    if not can_claim:
        await cq.message.answer(f"⏰ You've already claimed <b>{label}</b> today.\nCome back tomorrow!")
        return
    reward_str = await setting(reward_key)
    reward = int(reward_str) if reward_str.isdigit() else 0
    await add_coins(uid, reward)
    await mark_daily(uid, action)
    await log(uid, "claim", f"action={action}, +{reward}")
    await cq.message.answer(f"🎉 <b>+{reward} Coins</b> added for <b>{label}</b>!\n🪙 Keep earning!")


# Task claims
@router.callback_query(F.data == "claim_watch_ads")
async def cb_claim_watch_ads(cq: CallbackQuery):
    await _handle_claim(cq, "watch_ads", "reward_watch_ads", "Watch Ads")

@router.callback_query(F.data == "claim_join_tg")
async def cb_claim_join_tg(cq: CallbackQuery):
    await _handle_claim(cq, "join_tg", "reward_join_tg", "Join TG Channel")

@router.callback_query(F.data == "claim_follow_social")
async def cb_claim_follow_social(cq: CallbackQuery):
    await _handle_claim(cq, "follow_social", "reward_follow_social", "Follow Social")

@router.callback_query(F.data == "claim_subscribe_yt")
async def cb_claim_subscribe_yt(cq: CallbackQuery):
    await _handle_claim(cq, "subscribe_yt", "reward_subscribe_yt", "Subscribe YouTube")

@router.callback_query(F.data == "claim_rate_app")
async def cb_claim_rate_app(cq: CallbackQuery):
    await _handle_claim(cq, "rate_app", "reward_rate_app", "Rate Our App")

# Survey claims
@router.callback_query(F.data.startswith("claim_survey_"))
async def cb_claim_survey(cq: CallbackQuery):
    n = cq.data.split("_")[-1]
    await _handle_claim(cq, f"survey_{n}", f"reward_survey_{n}", f"Survey {n}")

# Bexacart claims
@router.callback_query(F.data.startswith("claim_bexacart_"))
async def cb_claim_bexacart(cq: CallbackQuery):
    n = cq.data.split("_")[-1]
    names = {"1": "Cloths", "2": "Mobiles", "3": "Accessories", "4": "Beauty", "5": "Others"}
    await _handle_claim(cq, f"bexacart_{n}", f"reward_bexacart_{n}", names.get(n, f"Category {n}"))

# Rewards section claims
@router.callback_query(F.data.startswith("claim_rewards_"))
async def cb_claim_rewards(cq: CallbackQuery):
    key = cq.data.replace("claim_rewards_", "")
    labels = {
        "vouchers": "My Vouchers", "double_points": "Double Points",
        "claim": "Claim Reward", "unlock": "Unlock Reward", "view": "View Rewards",
    }
    await _handle_claim(cq, f"rewards_{key}", f"reward_{key}", labels.get(key, key))


# =============================================================================
# WITHDRAW FLOW
# =============================================================================

@router.callback_query(F.data == "withdraw")
async def cb_withdraw(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    uid = cq.from_user.id
    user = await get_user(uid)
    min_wd_str = await setting("min_withdraw_coins")
    min_wd = int(min_wd_str) if min_wd_str.isdigit() else 1000
    if not user or user["coins"] < min_wd:
        rupees = await coins_to_rupees(min_wd)
        await cq.message.answer(
            f"❌ Minimum withdraw is <b>{min_wd} Coins</b> ({rupees}).\n"
            f"You have <b>{user['coins'] if user else 0} Coins</b>."
        )
        return
    await state.set_state(WithdrawStates.choosing_method)
    await cq.message.answer(
        "💸 <b>Withdraw</b>\nChoose your preferred withdrawal method:",
        reply_markup=kb_withdraw_method(),
    )


@router.callback_query(F.data == "withdraw_upi", WithdrawStates.choosing_method)
async def cb_withdraw_upi(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    await state.set_state(WithdrawStates.entering_upi)
    await cq.message.answer("🏦 Please enter your <b>UPI ID</b>:\n<i>e.g. name@bank</i>",
                            reply_markup=ReplyKeyboardRemove())


@router.message(WithdrawStates.entering_upi)
async def process_upi(message: Message, state: FSMContext):
    upi = message.text.strip()
    if "@" not in upi:
        await message.answer("⚠️ Invalid UPI ID. Please re-enter:")
        return
    uid = message.from_user.id
    user = await get_user(uid)
    coins = user["coins"] if user else 0
    wid = await create_withdrawal(uid, coins, "upi", upi)
    # Lock coins
    conn = get_db()
    conn.execute(
        "UPDATE users SET locked_coins=locked_coins+?, coins=MAX(0,coins-?) WHERE user_id=?",
        (coins, coins, uid)
    )
    conn.commit()
    conn.close()
    await state.clear()
    await message.answer(
        f"✅ Withdrawal request <b>#{wid}</b> submitted!\n"
        f"💰 Amount: <b>{coins} Coins</b>\n📬 UPI: <code>{upi}</code>\n\n"
        "⏳ Admin will process it soon.",
        reply_markup=kb_main_menu(),
    )
    await log(uid, "withdraw_request", f"wid={wid}, coins={coins}, upi={upi}")
    # Notify admin
    await bot.send_message(
        ADMIN_ID,
        f"📥 <b>New Withdrawal Request #{wid}</b>\n"
        f"👤 User: {message.from_user.full_name} (<code>{uid}</code>)\n"
        f"💰 Coins: {coins}\n🏦 UPI: <code>{upi}</code>",
        reply_markup=kb_approve_reject(wid),
    )


@router.callback_query(F.data == "withdraw_qr", WithdrawStates.choosing_method)
async def cb_withdraw_qr(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    await state.set_state(WithdrawStates.uploading_qr)
    await cq.message.answer("📸 Please send your <b>QR Code Screenshot</b>:",
                            reply_markup=ReplyKeyboardRemove())


@router.message(WithdrawStates.uploading_qr, F.photo)
async def process_qr(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    uid = message.from_user.id
    user = await get_user(uid)
    coins = user["coins"] if user else 0
    wid = await create_withdrawal(uid, coins, "qr", file_id)
    conn = get_db()
    conn.execute(
        "UPDATE users SET locked_coins=locked_coins+?, coins=MAX(0,coins-?) WHERE user_id=?",
        (coins, coins, uid)
    )
    conn.commit()
    conn.close()
    await state.clear()
    await message.answer(
        f"✅ Withdrawal request <b>#{wid}</b> submitted!\n"
        f"💰 Amount: <b>{coins} Coins</b>\n📸 QR Screenshot received.\n\n"
        "⏳ Admin will process it soon.",
        reply_markup=kb_main_menu(),
    )
    await log(uid, "withdraw_request", f"wid={wid}, coins={coins}, method=qr")
    await bot.send_photo(
        ADMIN_ID, photo=file_id,
        caption=(
            f"📥 <b>New Withdrawal Request #{wid}</b>\n"
            f"👤 User: {message.from_user.full_name} (<code>{uid}</code>)\n"
            f"💰 Coins: {coins}\n📸 QR Screenshot above"
        ),
        reply_markup=kb_approve_reject(wid),
    )


# ── Admin: approve/reject withdrawals ─────────────────────────────────────────
@router.callback_query(F.data.startswith("wd_approve_"))
async def cb_wd_approve(cq: CallbackQuery):
    if not await is_admin(cq.from_user.id):
        await cq.answer("❌ Not authorised", show_alert=True)
        return
    wid = int(cq.data.split("_")[-1])
    wd = await get_withdrawal(wid)
    if not wd:
        await cq.answer("Request not found.", show_alert=True)
        return
    if wd["status"] != "pending":
        await cq.answer(f"Already {wd['status']}.", show_alert=True)
        return
    # Deduct locked coins
    conn = get_db()
    conn.execute(
        "UPDATE users SET locked_coins=MAX(0,locked_coins-?) WHERE user_id=?",
        (wd["coins"], wd["user_id"])
    )
    conn.commit()
    conn.close()
    await update_withdrawal_status(wid, "approved")
    await cq.message.edit_reply_markup(reply_markup=None)
    await cq.message.reply(f"✅ Request #{wid} <b>Approved</b>.")
    try:
        await bot.send_message(
            wd["user_id"],
            f"🎉 <b>Withdrawal Approved!</b>\n"
            f"💰 <b>{wd['coins']} Coins</b> have been paid.\n"
            f"Method: <b>{wd['method'].upper()}</b>"
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("wd_reject_"))
async def cb_wd_reject(cq: CallbackQuery):
    if not await is_admin(cq.from_user.id):
        await cq.answer("❌ Not authorised", show_alert=True)
        return
    wid = int(cq.data.split("_")[-1])
    wd = await get_withdrawal(wid)
    if not wd:
        await cq.answer("Request not found.", show_alert=True)
        return
    if wd["status"] != "pending":
        await cq.answer(f"Already {wd['status']}.", show_alert=True)
        return
    # Return locked coins to available
    conn = get_db()
    conn.execute(
        "UPDATE users SET locked_coins=MAX(0,locked_coins-?), coins=coins+? WHERE user_id=?",
        (wd["coins"], wd["coins"], wd["user_id"])
    )
    conn.commit()
    conn.close()
    await update_withdrawal_status(wid, "rejected")
    await cq.message.edit_reply_markup(reply_markup=None)
    await cq.message.reply(f"❌ Request #{wid} <b>Rejected</b>. Coins returned.")
    try:
        await bot.send_message(
            wd["user_id"],
            f"😞 <b>Withdrawal Rejected</b>\n"
            f"Request #{wid} was rejected by admin.\n"
            f"💰 {wd['coins']} Coins have been returned to your balance."
        )
    except Exception:
        pass


# =============================================================================
# ADMIN PANEL CALLBACKS
# =============================================================================

def admin_only(func):
    """Decorator: reject non-admins silently."""
    async def wrapper(cq: CallbackQuery, *args, **kwargs):
        if not await is_admin(cq.from_user.id):
            await cq.answer("❌ Admin only.", show_alert=True)
            return
        return await func(cq, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


@router.callback_query(F.data == "adm_back")
@admin_only
async def cb_adm_back(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    await state.clear()
    await cq.message.edit_text("🛡 <b>Admin Panel</b>", reply_markup=kb_admin_panel())


@router.callback_query(F.data == "adm_dashboard")
@admin_only
async def cb_adm_dashboard(cq: CallbackQuery):
    await cq.answer()
    total, active, pending, banned = await stats()
    text = (
        f"📊 <b>Dashboard</b>\n\n"
        f"👥 Total Users   : <b>{total}</b>\n"
        f"🟢 Active Today  : <b>{active}</b>\n"
        f"⏳ Pending WDs   : <b>{pending}</b>\n"
        f"🚫 Banned Users  : <b>{banned}</b>"
    )
    await cq.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩ Back", callback_data="adm_back")]
    ]))


@router.callback_query(F.data == "adm_broadcast")
@admin_only
async def cb_adm_broadcast(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    await state.set_state(AdminStates.broadcast)
    await cq.message.answer("📣 Send the message you want to broadcast to all users:")


@router.message(AdminStates.broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    conn = get_db()
    users = conn.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()
    conn.close()
    sent = failed = 0
    for row in users:
        try:
            await bot.copy_message(row["user_id"], message.chat.id, message.message_id)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # rate limiting
    await message.answer(
        f"📣 Broadcast complete.\n✅ Sent: {sent}\n❌ Failed: {failed}",
        reply_markup=kb_admin_panel(),
    )


@router.callback_query(F.data == "adm_ban")
@admin_only
async def cb_adm_ban(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    await state.set_state(AdminStates.ban_user)
    await cq.message.answer("🚫 Enter the <b>User ID</b> to ban:")


@router.message(AdminStates.ban_user)
async def process_ban(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    try:
        uid = int(message.text.strip())
        conn = get_db()
        conn.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        await message.answer(f"🚫 User <code>{uid}</code> has been <b>banned</b>.", reply_markup=kb_admin_panel())
        try:
            await bot.send_message(uid, "🚫 You have been banned from this bot.")
        except Exception:
            pass
    except ValueError:
        await message.answer("⚠️ Invalid User ID.")


@router.callback_query(F.data == "adm_unban")
@admin_only
async def cb_adm_unban(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    await state.set_state(AdminStates.unban_user)
    await cq.message.answer("✅ Enter the <b>User ID</b> to unban:")


@router.message(AdminStates.unban_user)
async def process_unban(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    try:
        uid = int(message.text.strip())
        conn = get_db()
        conn.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        await message.answer(f"✅ User <code>{uid}</code> has been <b>unbanned</b>.", reply_markup=kb_admin_panel())
        try:
            await bot.send_message(uid, "✅ You have been unbanned. Use /start to continue.")
        except Exception:
            pass
    except ValueError:
        await message.answer("⚠️ Invalid User ID.")


@router.callback_query(F.data == "adm_edit_welcome")
@admin_only
async def cb_adm_edit_welcome(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    await state.set_state(AdminStates.edit_welcome)
    current = await setting("welcome_caption")
    await cq.message.answer(
        f"✏️ <b>Current Welcome Message:</b>\n\n{current}\n\n"
        "Send the <b>new welcome message</b>.\n"
        "Use <code>{name}</code> as placeholder for user's name."
    )


@router.message(AdminStates.edit_welcome)
async def process_edit_welcome(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    await set_setting("welcome_caption", message.text)
    await message.answer("✅ Welcome message updated!", reply_markup=kb_admin_panel())


@router.callback_query(F.data == "adm_edit_image")
@admin_only
async def cb_adm_edit_image(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    await state.set_state(AdminStates.edit_image)
    await cq.message.answer("🖼 Send the new <b>start image</b> (photo):")


@router.message(AdminStates.edit_image, F.photo)
async def process_edit_image(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    file_id = message.photo[-1].file_id
    await set_setting("start_image", file_id)
    await message.answer("✅ Start image updated!", reply_markup=kb_admin_panel())


@router.callback_query(F.data == "adm_edit_channels")
@admin_only
async def cb_adm_edit_channels(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    c1 = await setting("channel_1")
    c2 = await setting("channel_2")
    await cq.message.answer(
        f"📢 <b>Current Channels:</b>\n"
        f"1: <code>{c1}</code>\n"
        f"2: <code>{c2}</code>\n\n"
        "Send new <b>Channel 1</b> in format: <code>@username|https://t.me/username</code>"
    )
    await state.set_state(AdminStates.edit_channel_1)


@router.message(AdminStates.edit_channel_1)
async def process_channel_1(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await set_setting("channel_1", message.text.strip())
    await state.set_state(AdminStates.edit_channel_2)
    await message.answer("✅ Channel 1 saved.\nNow send new <b>Channel 2</b>:")


@router.message(AdminStates.edit_channel_2)
async def process_channel_2(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await set_setting("channel_2", message.text.strip())
    await state.clear()
    await message.answer("✅ Both channels updated!", reply_markup=kb_admin_panel())


@router.callback_query(F.data == "adm_edit_ref_bonus")
@admin_only
async def cb_adm_edit_ref_bonus(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    current = await setting("referral_bonus")
    await state.set_state(AdminStates.edit_referral_bonus)
    await cq.message.answer(f"💰 Current Referral Bonus: <b>{current} Coins</b>\nEnter new value:")


@router.message(AdminStates.edit_referral_bonus)
async def process_ref_bonus(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    val = message.text.strip()
    if not val.isdigit():
        await message.answer("⚠️ Please enter a valid number.")
        return
    await set_setting("referral_bonus", val)
    await message.answer(f"✅ Referral bonus set to <b>{val} Coins</b>.", reply_markup=kb_admin_panel())


@router.callback_query(F.data == "adm_edit_min_withdraw")
@admin_only
async def cb_adm_edit_min_withdraw(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    current = await setting("min_withdraw_coins")
    await state.set_state(AdminStates.edit_min_withdraw)
    await cq.message.answer(f"💵 Current Min Withdraw: <b>{current} Coins</b>\nEnter new value:")


@router.message(AdminStates.edit_min_withdraw)
async def process_min_withdraw(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    val = message.text.strip()
    if not val.isdigit():
        await message.answer("⚠️ Please enter a valid number.")
        return
    await set_setting("min_withdraw_coins", val)
    await message.answer(f"✅ Minimum withdraw set to <b>{val} Coins</b>.", reply_markup=kb_admin_panel())


@router.callback_query(F.data == "adm_edit_rewards")
@admin_only
async def cb_adm_edit_rewards(cq: CallbackQuery):
    await cq.answer()
    await cq.message.edit_text("🪙 <b>Edit Coin Rewards</b>\nSelect a reward to edit:",
                               reply_markup=kb_admin_rewards())


@router.callback_query(F.data.startswith("adm_reward_"))
@admin_only
async def cb_adm_select_reward(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    reward_key = cq.data.replace("adm_reward_", "")
    current = await setting(reward_key)
    await state.update_data(edit_key=reward_key)
    await state.set_state(AdminStates.edit_coin_reward)
    await cq.message.answer(
        f"🪙 <b>{reward_key}</b>\nCurrent: <b>{current} Coins</b>\nEnter new value:"
    )


@router.message(AdminStates.edit_coin_reward)
async def process_coin_reward(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    data = await state.get_data()
    reward_key = data.get("edit_key", "")
    await state.clear()
    val = message.text.strip()
    if not val.isdigit():
        await message.answer("⚠️ Please enter a valid number.")
        return
    await set_setting(reward_key, val)
    await message.answer(f"✅ <b>{reward_key}</b> set to <b>{val} Coins</b>.", reply_markup=kb_admin_panel())


@router.callback_query(F.data == "adm_edit_links")
@admin_only
async def cb_adm_edit_links(cq: CallbackQuery):
    await cq.answer()
    await cq.message.edit_text("🔗 <b>Edit Links</b>\nSelect a link to edit:",
                               reply_markup=kb_admin_links())


@router.callback_query(F.data.startswith("adm_link_"))
@admin_only
async def cb_adm_select_link(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    link_key = cq.data.replace("adm_link_", "")
    current = await setting(link_key)
    await state.update_data(edit_key=link_key)
    await state.set_state(AdminStates.edit_link)
    await cq.message.answer(
        f"🔗 <b>{link_key}</b>\nCurrent: <code>{current}</code>\nSend new URL:"
    )


@router.message(AdminStates.edit_link)
async def process_link(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    data = await state.get_data()
    link_key = data.get("edit_key", "")
    await state.clear()
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("⚠️ URL must start with http:// or https://")
        return
    await set_setting(link_key, url)
    await message.answer(f"✅ <b>{link_key}</b> updated.", reply_markup=kb_admin_panel())


@router.callback_query(F.data == "adm_logs")
@admin_only
async def cb_adm_logs(cq: CallbackQuery):
    await cq.answer()
    conn = get_db()
    rows = conn.execute(
        "SELECT user_id, action, detail, created_at FROM logs ORDER BY id DESC LIMIT 20"
    ).fetchall()
    conn.close()
    if not rows:
        await cq.message.answer("📋 No logs yet.", reply_markup=kb_admin_panel())
        return
    lines = [f"<b>{r['created_at'][:16]}</b> | {r['user_id']} | {r['action']} | {r['detail']}"
             for r in rows]
    await cq.message.answer(
        "📋 <b>Last 20 Logs:</b>\n\n" + "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩ Back", callback_data="adm_back")]
        ]),
    )


@router.callback_query(F.data == "adm_pending_wd")
@admin_only
async def cb_adm_pending_wd(cq: CallbackQuery):
    await cq.answer()
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM withdrawals WHERE status='pending' ORDER BY id DESC LIMIT 10"
    ).fetchall()
    conn.close()
    if not rows:
        await cq.message.answer("⏳ No pending withdrawals.", reply_markup=kb_admin_panel())
        return
    for wd in rows:
        text = (
            f"📥 <b>Request #{wd['id']}</b>\n"
            f"👤 User ID: <code>{wd['user_id']}</code>\n"
            f"💰 Coins: <b>{wd['coins']}</b>\n"
            f"📬 Method: <b>{wd['method'].upper()}</b>\n"
            f"📝 Detail: <code>{wd['detail'] if wd['method']=='upi' else 'QR Photo'}</code>\n"
            f"🕐 Requested: {wd['requested_at'][:16]}"
        )
        if wd["method"] == "qr":
            await bot.send_photo(
                cq.from_user.id, photo=wd["detail"],
                caption=text, reply_markup=kb_approve_reject(wd["id"])
            )
        else:
            await cq.message.answer(text, reply_markup=kb_approve_reject(wd["id"]))


# =============================================================================
# ERROR HANDLER
# =============================================================================

@dp.error()
async def error_handler(event, exception: Exception):
    logger.error(f"Unhandled error: {exception}", exc_info=True)
    try:
        # Try to notify admin
        await bot.send_message(ADMIN_ID, f"⚠️ Bot Error:\n<code>{str(exception)[:500]}</code>")
    except Exception:
        pass


# =============================================================================
# STARTUP / SHUTDOWN
# =============================================================================

async def on_startup():
    init_db()
    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username}")
    try:
        await bot.send_message(ADMIN_ID, f"✅ Bot <b>@{me.username}</b> started successfully.")
    except Exception:
        pass


async def on_shutdown():
    logger.info("Bot shutting down.")
    await bot.session.close()


# =============================================================================
# MAIN
# =============================================================================

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())

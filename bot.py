import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Force Join Channels
CHANNELS = [
    "@Moneyearning_updates",
    "@your_channel2_username"
]


@dp.message(Command("start"))
async def start(message: types.Message):

    caption = (
        f"✦ Welcome to {message.from_user.first_name} ✦\n\n"
        "❖ Complete Simple Task\n"
        "❖ Earn ₹250 Rewards\n"
        "❖ Join 2 Official Channels\n"
        "❖ Unlock Bot Access\n"
        "❖ Tap Verify After Joining"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➜ 𝗝𝗼𝗶𝗻 𝟭",
                    url="https://t.me/Moneyearning_updates"
                ),
                InlineKeyboardButton(
                    text="➜ 𝗝𝗼𝗶𝗻 𝟮",
                    url="https://t.me/+L4ubY08PrhtmZDI9"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➲ 𝐕𝐄𝐑𝐈𝐅𝐘",
                    callback_data="verify"
                )
            ]
        ]
    )

    await message.answer_photo(
        photo="https://images.unsplash.com/photo-1633158829585-23ba8f7c8caf?q=80&w=500",
        caption=caption,
        reply_markup=keyboard
    )


@dp.callback_query(F.data == "verify")
async def verify(call: CallbackQuery):

    not_joined = []

    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(
                chat_id=channel,
                user_id=call.from_user.id
            )

            if member.status in ["left", "kicked"]:
                not_joined.append(channel)

        except Exception as e:
            logging.error(e)
            not_joined.append(channel)

    if len(not_joined) == 0:

        await call.answer(
            "✅ Verification Successful",
            show_alert=True
        )

        await call.message.answer(
            "🎉 Congratulations!\n\n"
            "Your verification is completed successfully.\n"
            "Now you can use the bot."
        )

    else:

        await call.answer(
            "❌ Please join all required channels first!",
            show_alert=True
        )


async def main():
    print("Bot Started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging
import os
from dataclasses import dataclass

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from dotenv import load_dotenv


load_dotenv()
logging.basicConfig(level=logging.INFO)


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: set[int]


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is required")
    raw_admins = os.getenv("ADMIN_IDS", "").replace(" ", "")
    admins = {int(x) for x in raw_admins.split(",") if x}
    return Config(bot_token=token, admin_ids=admins)


router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    text = (
        "Hi. I am ready.\n\n"
        "Commands:\n"
        "/help - show help\n"
        "/id - show your Telegram id\n"
        "/status - bot status"
    )
    await message.answer(text)


@router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer("Send me a message and I will echo it. Add your own handlers in bot.py.")


@router.message(Command("id"))
async def id_cmd(message: Message) -> None:
    await message.answer(f"Your id: {message.from_user.id}")


@router.message(Command("status"))
async def status_cmd(message: Message) -> None:
    await message.answer("Bot is running.")


@router.message(F.text)
async def echo(message: Message) -> None:
    await message.answer(message.text)


async def main() -> None:
    config = load_config()
    bot = Bot(token=config.bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

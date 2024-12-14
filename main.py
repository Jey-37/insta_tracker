import asyncio

import instaloader
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from handlers import router
from middleware import UserIdMiddleware
from utils import load_user_data, save_user_data


async def main():
    data = load_user_data()
    loader = instaloader.Instaloader()
    if data.get("session") and data.get("username"):
        loader.load_session(data["username"], data["session"])

    dp = Dispatcher(loader=loader)
    dp.include_router(router)
    dp.update.outer_middleware(UserIdMiddleware())

    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    commands = [
        BotCommand(command="track", description="Add a profile to your subscriptions"),
        BotCommand(command="untrack", description="Remove a profile from your subscriptions"),
        BotCommand(command="my_subs", description="Show your active subscriptions"),
        BotCommand(command="check", description="Check new posts from your subscriptions"),
        BotCommand(command="login", description="Sign in")
    ]
    await bot.set_my_commands(commands)
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        if loader.context.is_logged_in:
            data = load_user_data()
            data["username"] = loader.context.username
            data["session"] = loader.save_session()
            save_user_data(data)


if __name__ == "__main__":
    asyncio.run(main())

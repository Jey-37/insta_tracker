import json
import random
import logging
import asyncio
from datetime import datetime

import instaloader
from instaloader.exceptions import *
from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandObject, CommandStart, StateFilter
from aiogram.utils.chat_action import ChatActionSender
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import DATA_FILE, USER_POSTS_FETCH_DELAY
from exceptions import InstagramException
from states import Login
from utils import *


router = Router()

@router.message(CommandStart())
async def start_command_handler(message: Message):
    await message.answer("Hello!")


@router.message(Command("track"))
async def track_command_handler(
            message: Message, 
            command: CommandObject, 
            bot: Bot,
            loader: instaloader.Instaloader):
    username = command.args

    if not username:
        await message.answer("Please, provide an instagram username as a parameter of the command")
        return

    if not is_valid_profile_name(username):
        await message.answer("Wrong username format!")
        return

    data = load_user_data()

    if username in data["profiles"]:
        await message.answer("You are already subscribed on the user")
        return

    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        try:
            new_posts = await run_sync_in_executor(get_new_user_posts, loader, username)

            data["profiles"][username] = int(get_current_utc_datetime().timestamp())
            save_user_data(data)
    
            await message.answer("Subscription successfully created!")
            if new_posts:
                await answer_post(message, new_posts[0])
        except InstagramException as ex:
            await message.answer(str(ex))
        except Exception as ex:
            logging.error(str(ex), exc_info=True)
            await message.answer("Failed to create a subscription...")


@router.message(Command("my_subs"))
async def my_subs_command_handler(message: Message):
    data = load_user_data()

    if not data["profiles"]:
        await message.answer("You have no subscriptions")
        return
    
    await message.answer(
        "You track the following users:\n" + "\n".join(list(data["profiles"].keys())))


@router.message(Command("untrack"))
async def untrack_command_handler(message: Message, command: CommandObject):
    username = command.args

    if not username:
        await message.answer("Please, provide an instagram username as a parameter of the command")
        return

    data = load_user_data()

    if username not in data["profiles"]:
        await message.answer("You are not subscribed on the user")
        return

    del data["profiles"][username]
    save_user_data(data)
    
    await message.answer("Subscription on user successfully removed!")


@router.message(Command("check"))
async def check_command_handler(message: Message, loader: instaloader.Instaloader):
    data = load_user_data()

    if not data["profiles"]:
        await message.answer("You don't have any subscriptions yet")
        return

    if data["checking"]:
        await message.answer("You can't use two /check commands simultaneously")
        return

    data["checking"] = True
    save_user_data(data)

    user_subs = data["profiles"]

    await message.answer("Fetching posts (be patient, it might take a while) ...")
    for i, username in enumerate(user_subs):
        try:
            curr_timestamp = int(get_current_utc_datetime().timestamp())
            profile_posts = get_new_user_posts(
                loader = loader,
                username = username, 
                after_date = datetime.fromtimestamp(user_subs[username]))

            if profile_posts:
                await message.answer(f"<b>{username}</b> published some new posts ⬇️")
                for post in profile_posts:
                    await answer_post(message, post)

            user_subs[username] = curr_timestamp
            save_user_data(data)

            if i < len(user_subs)-1:
                await asyncio.sleep(random.randint(USER_POSTS_FETCH_DELAY-20, USER_POSTS_FETCH_DELAY+20))
        except InstagramException as ex:
            await message.answer(f"An error occured with profile {username}: {ex}")
        except Exception as ex:
            logging.error(f"{username}:\n{ex}", exc_info=True)
            await message.answer(f"Failed to fetch recent posts of profile {username}")

    data["checking"] = False
    save_user_data(data)

    await message.answer("Fetching recent posts completed 😮‍💨")


@router.message(Command("login"))
async def login_command_handler(
            message: Message, 
            command: CommandObject, 
            state: FSMContext,
            bot: Bot,
            loader: instaloader.Instaloader):
    if loader.context.is_logged_in:
        await message.answer("You're already signed in")
        return

    try:
        user, password = command.args.split()
    except:
        await message.answer("Wrong command arguments")
        return

    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        try:
            await run_sync_in_executor(loader.login, user, password)

            await message.answer("You've successfully signed in!")
        except BadCredentialsException:
            await message.answer("Wrong password")
        except TwoFactorAuthRequiredException:
            await message.answer("First step of 2FA login done. Now enter your 2FA code.")
            await state.set_state(Login.two_factor_auth)
        except LoginException as ex:
            logging.error(str(ex), exc_info=True)
            await message.answer("An error happened during login (e.g. the provided username might not exist)")


@router.message(Login.two_factor_auth, F.text)
async def two_factor_code_handler(
            message: Message, 
            state: FSMContext,
            bot: Bot,
            loader: instaloader.Instaloader):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        try:
            await run_sync_in_executor(loader.two_factor_login, message.text)

            await state.clear()
            await message.answer("You've successfully signed in!")
        except BadCredentialsException:
            await message.answer("Verification code is invalid")

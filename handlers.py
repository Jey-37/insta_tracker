import json
import random
from datetime import datetime

from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message

from config import dp, bot, DATA_FILE, USER_POSTS_FETCH_DELAY
from exceptions import InstagramException
from utils import *


@dp.message(CommandStart())
async def start_command_handler(message: Message):
    with open(DATA_FILE, 'r') as file:
        data = json.load(file)

    chat_id = str(message.chat.id)

    if chat_id not in data:
        data[chat_id] = {
            "profiles": {},
            "checking": False
        }

        with open(DATA_FILE, 'w') as file:
            json.dump(data, file)

    await message.answer("Hello!")


@dp.message(Command("track"))
async def track_command_handler(message: Message, command: CommandObject):
    username = command.args

    if not username:
        await message.answer("Please, provide an instagram username as a parameter of the command")
        return

    if not is_valid_string(username):
        await message.answer("Wrong username format!")
        return

    with open(DATA_FILE, 'r') as file:
        data = json.load(file)

    chat_id = str(message.chat.id)

    if username in data[chat_id]["profiles"]:
        await message.answer("You are already subscribed on the user")
        return

    await bot.send_chat_action(chat_id = message.chat.id, action = 'typing')
    try:
        new_posts = await get_new_user_posts(username)

        data[chat_id]["profiles"][username] = int(get_current_utc_datetime().timestamp())
        with open(DATA_FILE, 'w') as file:
            json.dump(data, file)
    
        await message.answer("Subscription successfully created!")
        if new_posts:
            await answer_post(message, new_posts[0])
    except InstagramException as ex:
        await message.answer(ex)
    except Exception as ex:
        print(ex)
        await message.answer("Failed to create a subscription...")


@dp.message(Command("my_subs"))
async def my_subs_command_handler(message: Message):
    with open(DATA_FILE, 'r') as file:
        data = json.load(file)

    chat_id = str(message.chat.id)

    if not data.get(chat_id):
        await message.answer("You have no subscriptions")
        return
    
    await message.answer(
        "You track the following users:\n" + "\n".join(list(data[chat_id]["profiles"].keys())))


@dp.message(Command("untrack"))
async def untrack_command_handler(message: Message, command: CommandObject):
    username = command.args

    if not username:
        await message.answer("Please, provide an instagram username as a parameter of the command")
        return

    if not is_valid_string(username):
        await message.answer("Wrong username format!")
        return

    with open(DATA_FILE, 'r') as file:
        data = json.load(file)

    chat_id = str(message.chat.id)

    if username not in data[chat_id]["profiles"]:
        await message.answer("You are not subscribed on the user")
        return

    del data[chat_id]["profiles"][username]
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file)
    
    await message.answer("Subscription on user successfully removed!")


@dp.message(Command("check"))
async def check_command_handler(message: Message):
    with open(DATA_FILE, 'r') as file:
        data = json.load(file)

    chat_id = str(message.chat.id)

    if not data.get(chat_id):
        await message.answer("You don't have any subscriptions yet")
        return

    if data[chat_id]["checking"]:
        await message.answer("You can't use two /check commands simultaneously")
        return

    data[chat_id]["checking"] = True
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file)

    user_subs = data[chat_id]["profiles"]

    await message.answer("Fetching posts (be patient, it might take a while) ...")
    for i, username in enumerate(user_subs):
        try:
            curr_timestamp = int(get_current_utc_datetime().timestamp())
            profile_posts = await get_new_user_posts(
                username = username, 
                after_date = datetime.fromtimestamp(user_subs[username]))

            if profile_posts:
                await message.answer(f"<b>{username}</b> published some new posts ⬇️")
            for post in profile_posts:
                await answer_post(message, post)

            user_subs[username] = curr_timestamp
            with open(DATA_FILE, 'w') as file:
                json.dump(data, file)

            if i < len(user_subs)-1:
                await asyncio.sleep(random.randint(USER_POSTS_FETCH_DELAY-20, USER_POSTS_FETCH_DELAY+20))
        except InstagramException as ex:
            await message.answer(f"An error occured with profile {username}: {ex}")
        except Exception as ex:
            print(f"{username}:\n{ex}")
            await message.answer(f"Failed to fetch recent posts of profile {username}")

    data[chat_id]["checking"] = False
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file)

    await message.answer("Fetching recent posts completed 😮‍💨")

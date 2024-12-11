import os
import logging

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import instaloader


logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s  %(levelname)s %(name)s: %(message)s", 
    datefmt='%I:%M:%S')

logging.getLogger("asyncio").setLevel(logging.WARNING)


load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

dp = Dispatcher()
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

DATA_FILE = "data.json"
if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
    with open(DATA_FILE, 'w') as file:
        file.write('{}')

loader = instaloader.Instaloader()

POST_FETCH_DELAY = 0.3
USER_POSTS_FETCH_DELAY = 60

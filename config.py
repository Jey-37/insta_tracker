import logging

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s  %(levelname)s %(name)s: %(message)s", 
    datefmt='%I:%M:%S')

logging.getLogger("asyncio").setLevel(logging.WARNING)


import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

DATA_FILE = "data.json"
if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
    with open(DATA_FILE, 'w') as file:
        file.write('{}')


POST_FETCH_DELAY = 0.3
USER_POSTS_FETCH_DELAY = 60

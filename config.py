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
USER_ID = os.getenv('USER_ID')

import json

DATA_FILE = "data.json"
try:
    with open(DATA_FILE, 'r') as file:
        json.load(file)
except:
    init_data = {
        "profiles": {},
        "checking": False
    }
    with open(DATA_FILE, 'w') as file:
        json.dump(init_data, file)

POST_FETCH_DELAY = 0.3
USER_POSTS_FETCH_DELAY = 60

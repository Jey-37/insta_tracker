import re
import time
import json
import asyncio
from typing import Optional
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor

import instaloader
from instaloader.exceptions import ProfileNotExistsException
from aiogram import html
from aiogram.types import (
    Message, 
    InlineKeyboardMarkup, InlineKeyboardButton, 
    InputMediaVideo, InputMediaPhoto)

from exceptions import InstagramException
from config import POST_FETCH_DELAY, DATA_FILE


def get_new_user_posts(
            loader: instaloader.Instaloader, 
            username: str, 
            after_date: Optional[datetime] = None) -> list[instaloader.Post]:
    try:
        profile = instaloader.Profile.from_username(loader.context, username)
    except ProfileNotExistsException:
        raise InstagramException(f"Profile wasn't found or it is restricted")

    if profile.mediacount == 0:
        raise InstagramException("No posts were found for this user")

    if profile.is_private:
        raise InstagramException("The user's profile is privat")

    TOP_POSTS_NUM = 4
    posts = []
    for post in profile.get_posts():
        posts.append(post)

        if len(posts) == TOP_POSTS_NUM:
            posts.sort(key=lambda p: p.date_utc, reverse=True)

            if not after_date:
                return posts[:1]

            for i in range(len(posts)):
                if posts[i].date_utc < after_date:
                    return posts[:i]

        if len(posts) > TOP_POSTS_NUM and post.date_utc < after_date:
            return posts[:-1]

        time.sleep(POST_FETCH_DELAY)

    return posts


executor_pool = ThreadPoolExecutor()

async def run_sync_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor_pool, func, *args)


def is_valid_profile_name(s: str) -> bool: 
    return bool(re.fullmatch(r'[\w.]+', s))


def get_current_utc_datetime() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def answer_post(message: Message, post: instaloader.Post) -> None:
    markup = InlineKeyboardMarkup(inline_keyboard =
        [[InlineKeyboardButton(
                text = "Check it out", 
                url = f"https://www.instagram.com/p/{post.shortcode}/")]])

    match post.typename:
        case 'GraphSidecar':
            media = []
            for node in post.get_sidecar_nodes():
                if node.is_video:
                    media.append(InputMediaVideo(media = node.video_url))
                else:
                    media.append(InputMediaPhoto(media = node.display_url))

            media[0].caption = build_message_text(post, with_url = True)

            await message.answer_media_group(media = media)
        case 'GraphVideo':
            await message.answer_video(
                video = post.video_url,
                caption = build_message_text(post),
                reply_markup = markup)
        case 'GraphImage':
            await message.answer_photo(
                photo = post.url,
                caption = build_message_text(post),
                reply_markup = markup)


def build_message_text(post: instaloader.Post, with_url: bool = False) -> str:
    text = post.caption + '\n\n'
    text += html.bold(f"{post.likes} ❤️    {post.comments} 💬")
    if post.video_view_count:
        text += html.bold(f"    {post.video_view_count} 👁")
    text += '\n\n'

    tdiff = get_current_utc_datetime() - post.date_utc
    text += html.italic(f"{post.date_utc.strftime('%d.%m %H:%M')} ({build_time_diff_string(tdiff)})")

    if with_url:
        text += "\n\n" + html.link(html.underline("Check it out"), f"https://www.instagram.com/p/{post.shortcode}/")

    return text


def build_time_diff_string(timediff: timedelta) -> str:
    s = ""
    if timediff.days > 0:
        s += f"{timediff.days} days "
    if timediff.seconds // 3600 > 0:
        s += f"{timediff.seconds // 3600} hours "
    s += f"{(timediff.seconds // 60) % 60} minutes ago"

    return s


def load_user_data(chat_id: int | str) -> Optional[dict]:
    init_data = {
        "profiles": {},
        "checking": False
    }
    with open(DATA_FILE, 'r') as file:
        return json.load(file).get(str(chat_id), init_data)


def save_user_data(chat_id: int | str, user_data: dict) -> None:
    with open(DATA_FILE, 'r+') as file:
        data = json.load(file)

        data[str(chat_id)] = user_data

        file.seek(0)
        json.dump(data, file)

        file.truncate()

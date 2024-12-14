from typing import Any
from aiogram import BaseMiddleware
from config import USER_ID


class UserIdMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict[str, Any]) -> Any:
        if str(data['event_from_user'].id) == USER_ID:
            return await handler(event, data)

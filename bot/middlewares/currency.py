"""Currency middleware: adds USD/RUB rate to data for English users."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types import User as AiogramUser

from bot.database.queries import users as users_queries
from bot.utils.currency import get_usd_rate


class CurrencyMiddleware(BaseMiddleware):
    """
    Middleware that fetches USD/RUB exchange rate and adds it to data.
    Only for users with language = 'en'.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Get user from event
        user: AiogramUser | None = None
        if hasattr(event, "from_user"):
            user = event.from_user

        if user and not user.is_bot:
            # Get user's language preference
            db_user = await users_queries.get_user(user.id)
            if db_user and db_user.language == "en":
                # For English users, add USD rate to data
                data["usd_rate"] = await get_usd_rate()
            else:
                # For non-English, add None (handlers will use RUB formatting)
                data["usd_rate"] = None
        else:
            data["usd_rate"] = None

        return await handler(event, data)

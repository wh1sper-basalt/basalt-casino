"""DemoRestoreMiddleware: set data['need_demo_restore'] when demo_mode and demo_balance < min_bet."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Dict

from aiogram import BaseMiddleware
from aiogram.types import Update

from bot.database.queries import settings as settings_queries
from bot.database.queries import users as users_queries
from bot.utils.logger import get_logger

log = get_logger(__name__)


def _get_user_id(event: Update) -> int | None:
    """Extract user id from Update."""
    obj = event.message or event.callback_query
    if obj is None or not hasattr(obj, "from_user") or not obj.from_user:
        return None
    return obj.from_user.id


class DemoRestoreMiddleware(BaseMiddleware):
    """
    If user has demo_mode and demo_balance < min_bet, set data['need_demo_restore'] = True.
    Handlers can use this to show restore button or redirect.
    """

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, object]], Awaitable[object]],
        event: Update,
        data: Dict[str, object],
    ) -> object:
        data.setdefault("need_demo_restore", False)
        user_id = _get_user_id(event)
        if user_id is None:
            return await handler(event, data)
        try:
            settings = await settings_queries.get_settings()
            balance_row = await users_queries.get_user_balance(user_id)
        except Exception:
            return await handler(event, data)
        if balance_row is None:
            return await handler(event, data)
        if balance_row.demo_mode and balance_row.demo_balance < settings.min_bet:
            data["need_demo_restore"] = True
        return await handler(event, data)

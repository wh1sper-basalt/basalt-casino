"""LoggingMiddleware: log every update (user_id, type) at DEBUG level."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Dict

from aiogram import BaseMiddleware
from aiogram.types import Update

from bot.utils.logger import get_logger

log = get_logger(__name__)


def _get_event_type_and_user(event: Update) -> tuple[str, int | None]:
    """Return (event_type, user_id)."""
    if event.message:
        uid = event.message.from_user.id if event.message.from_user else None
        return "message", uid
    if event.callback_query:
        uid = event.callback_query.from_user.id if event.callback_query.from_user else None
        return "callback_query", uid
    if event.inline_query:
        uid = event.inline_query.from_user.id if event.inline_query.from_user else None
        return "inline_query", uid
    return "update", None


class LoggingMiddleware(BaseMiddleware):
    """Log incoming update type and user_id at DEBUG."""

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, object]], Awaitable[object]],
        event: Update,
        data: Dict[str, object],
    ) -> object:
        event_type, user_id = _get_event_type_and_user(event)
        log.debug("update: type={}, user_id={}", event_type, user_id)
        return await handler(event, data)

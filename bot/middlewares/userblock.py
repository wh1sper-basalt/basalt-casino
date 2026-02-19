"""UserBlockMiddleware: full block = only stats (/info, /help); partial = no real mode, no withdraw."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Dict, cast

from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from bot.database.queries import users as users_queries
from bot.templates.texts import get_text
from bot.utils.logger import get_logger

log = get_logger(__name__)


def _get_user_id(event: TelegramObject) -> int | None:
    """Extract user id from Update."""
    if isinstance(event, Update):
        obj = event.message or event.callback_query
    else:
        obj = event
    if obj is None or not hasattr(obj, "from_user") or not obj.from_user:
        return None
    return obj.from_user.id


def _get_chat_id(event: TelegramObject) -> int | None:
    """Extract chat_id for reply."""
    if isinstance(event, Update):
        obj = event.message or event.callback_query
    else:
        obj = event
    if obj is None:
        return None
    if isinstance(obj, Message) and obj.chat:
        return obj.chat.id
    if isinstance(obj, CallbackQuery) and obj.message and obj.message.chat:
        return obj.message.chat.id
    return None


def _is_allowed_when_full_block(event: TelegramObject) -> bool:
    """Allow only /info, /help and stats-related callbacks when block_type=full."""
    if isinstance(event, Update):
        obj = event.message or event.callback_query
    else:
        obj = event
    if isinstance(obj, Message) and obj.text:
        text = (obj.text or "").strip()
        if text in ("/info", "/help"):
            return True
        return False
    if isinstance(obj, CallbackQuery) and obj.data:
        # Allow callbacks that only view stats (menu:stats, stats:*, etc.)
        data = (obj.data or "").strip()
        if data.startswith("stats:") or data == "menu:stats":
            return True
        return False
    return False


def _is_restricted_when_partial_block(event: TelegramObject) -> bool:
    """True if this event is switching to real mode or withdraw (block when partial)."""
    if isinstance(event, Update):
        obj = event.callback_query
    else:
        obj = event if isinstance(event, CallbackQuery) else None
    if not isinstance(obj, CallbackQuery) or not obj.data:
        return False
    data = (obj.data or "").strip()
    # Block: switch to real mode, withdraw menu/action
    if data.startswith("mode:") and "real" in data:
        return True
    if "withdraw" in data.lower():
        return True
    return False


async def _get_chat_id_and_lang(event: TelegramObject, user_id: int) -> tuple[int | None, str]:
    """Get chat_id and user language."""
    chat_id = _get_chat_id(event)
    lang = "en"
    user = await users_queries.get_user(user_id)
    if user:
        lang = user.language
    return chat_id, lang


class UserBlockMiddleware(BaseMiddleware):
    """
    If user is_blocked: full -> allow only /info, /help, stats view; partial -> block real mode and withdraw.
    """

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, object]], Awaitable[object]],
        event: Update,
        data: Dict[str, object],
    ) -> object:
        user_id = _get_user_id(event)
        if user_id is None:
            return await handler(event, data)

        user = await users_queries.get_user(user_id)
        if not user or not user.is_blocked:
            return await handler(event, data)

        block_type = (user.block_type or "").strip().lower()

        if block_type == "full":
            if _is_allowed_when_full_block(event):
                return await handler(event, data)
            chat_id, lang = await _get_chat_id_and_lang(event, user_id)
            if chat_id is not None and "bot" in data:
                await cast(Bot, data["bot"]).send_message(chat_id, get_text("block_full", lang))
            return

        if block_type == "partial":
            if _is_restricted_when_partial_block(event):
                chat_id, lang = await _get_chat_id_and_lang(event, user_id)
                if chat_id is not None and "bot" in data:
                    await cast(Bot, data["bot"]).send_message(chat_id, get_text("block_partial", lang))
                return

        return await handler(event, data)

"""TechWorkMiddleware: block by tech_works_global / tech_works_demo / tech_works_real."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Dict, cast

from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from bot.config import get_config
from bot.database.queries import settings as settings_queries
from bot.database.queries import users as users_queries
from bot.templates.texts import get_text
from bot.utils.logger import get_logger

log = get_logger(__name__)


def _get_user_id(event: TelegramObject) -> int | None:
    """Extract user id from Update (message or callback_query)."""
    if isinstance(event, Update):
        obj = event.message or event.callback_query
    else:
        obj = event
    if obj is None:
        return None
    if hasattr(obj, "from_user") and obj.from_user:
        return obj.from_user.id
    return None


async def _get_chat_id_and_lang(event: TelegramObject, user_id: int | None) -> tuple[int | None, str]:
    """Get chat_id for reply and user language. Returns (chat_id, lang)."""
    if isinstance(event, Update):
        obj = event.message or event.callback_query
    else:
        obj = event
    chat_id = None
    if isinstance(obj, Message):
        chat_id = obj.chat.id if obj.chat else None
    elif isinstance(obj, CallbackQuery):
        chat_id = obj.message.chat.id if obj.message and obj.message.chat else None
    lang = "en"
    if user_id:
        user = await users_queries.get_user(user_id)
        if user:
            lang = user.language
    return chat_id, lang


class TechWorkMiddleware(BaseMiddleware):
    """
    Read settings; if tech_works_global block non-admins; if tech_works_demo/real
    block the corresponding mode. Sends message and does not call handler when blocking.
    """

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, object]], Awaitable[object]],
        event: Update,
        data: Dict[str, object],
    ) -> object:
        user_id = _get_user_id(event)
        config = get_config()
        admin_ids = config.get_admin_ids()
        is_admin = user_id is not None and user_id in admin_ids

        try:
            settings = await settings_queries.get_settings()
        except Exception as e:
            log.warning("TechWork: could not load settings: {}", e)
            return await handler(event, data)

        if settings.tech_works_global:
            if not is_admin:
                chat_id, lang = await _get_chat_id_and_lang(event, user_id)
                if chat_id is not None and "bot" in data:
                    await cast(Bot, data["bot"]).send_message(
                        chat_id,
                        get_text("tech_works_global", lang),
                    )
                return
            return await handler(event, data)

        if user_id is None:
            return await handler(event, data)

        if settings.tech_works_demo or settings.tech_works_real:
            balance_row = await users_queries.get_user_balance(user_id)
            if balance_row is None:
                return await handler(event, data)
            demo_mode = balance_row.demo_mode
            if settings.tech_works_demo and demo_mode:
                chat_id, lang = await _get_chat_id_and_lang(event, user_id)
                if chat_id is not None and "bot" in data:
                    await cast(Bot, data["bot"]).send_message(
                        chat_id,
                        get_text("tech_works_demo", lang),
                    )
                return
            if settings.tech_works_real and not demo_mode:
                chat_id, lang = await _get_chat_id_and_lang(event, user_id)
                if chat_id is not None and "bot" in data:
                    await cast(Bot, data["bot"]).send_message(
                        chat_id,
                        get_text("tech_works_real", lang),
                    )
                return

        return await handler(event, data)

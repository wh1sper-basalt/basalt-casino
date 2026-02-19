"""Inject bot instance into handler data so other middlewares can send messages."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import Update


class BotInjectMiddleware(BaseMiddleware):
    """Set data['bot'] so TechWork/UserBlock can send messages when blocking."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, object]], Awaitable[object]],
        event: Update,
        data: Dict[str, object],
    ) -> object:
        data["bot"] = self.bot
        return await handler(event, data)

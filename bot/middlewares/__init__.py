"""Middlewares: BotInject, TechWork, UserBlock, DemoRestore, Logging, Currency. Register in this order."""

from bot.middlewares.bot_inject import BotInjectMiddleware
from bot.middlewares.currency import CurrencyMiddleware
from bot.middlewares.demo import DemoRestoreMiddleware
from bot.middlewares.logging_mw import LoggingMiddleware
from bot.middlewares.techwork import TechWorkMiddleware
from bot.middlewares.userblock import UserBlockMiddleware

__all__ = [
    "BotInjectMiddleware",
    "TechWorkMiddleware",
    "UserBlockMiddleware",
    "DemoRestoreMiddleware",
    "LoggingMiddleware",
    "CurrencyMiddleware",
]

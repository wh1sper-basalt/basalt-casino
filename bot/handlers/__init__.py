"""Routers: start, info_help, user, games, bet, payments, admin."""

from aiogram import Router

from bot.handlers.admin import router as admin_router
from bot.handlers.bet import router as bet_router
from bot.handlers.games import router as games_router
from bot.handlers.info_help import router as info_help_router
from bot.handlers.payments import router as payments_router
from bot.handlers.start import router as start_router
from bot.handlers.user import router as user_router
from bot.handlers.user.referral import router as referral_router


def get_root_router() -> Router:
    """Assemble all routers into one. Order: start, info_help, user, games, bet, payments, admin."""
    root = Router()
    root.include_router(start_router)
    root.include_router(info_help_router)
    root.include_router(user_router)
    root.include_router(games_router)
    root.include_router(bet_router)
    root.include_router(payments_router)
    root.include_router(admin_router)
    root.include_router(referral_router)
    return root

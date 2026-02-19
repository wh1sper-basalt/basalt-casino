"""User: profile, settings, stats."""

from aiogram import Router

from bot.handlers.user.profile import router as profile_router
from bot.handlers.user.settings import router as settings_router
from bot.handlers.user.stats import router as stats_router

router = Router(name="user")
router.include_router(profile_router)
router.include_router(settings_router)
router.include_router(stats_router)

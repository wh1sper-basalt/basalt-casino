"""Admin: panel, users, settings, payments, stats, broadcast."""

from aiogram import Router

from bot.handlers.admin.broadcast import router as broadcast_router
from bot.handlers.admin.panel import router as panel_router
from bot.handlers.admin.payments import router as payments_router
from bot.handlers.admin.settings import router as settings_router
from bot.handlers.admin.stats import router as stats_router
from bot.handlers.admin.users import router as users_router

router = Router(name="admin")
router.include_router(panel_router)
router.include_router(users_router)
router.include_router(settings_router)
router.include_router(payments_router)
router.include_router(stats_router)
router.include_router(broadcast_router)

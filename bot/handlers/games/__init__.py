"""Games: list, flow (outcome, amount, confirm, place_bet), result."""

from aiogram import Router

from bot.handlers.games.flow import router as flow_router
from bot.handlers.games.list_handler import router as list_router

router = Router(name="games")
router.include_router(list_router)
router.include_router(flow_router)

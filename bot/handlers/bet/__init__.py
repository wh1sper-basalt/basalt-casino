"""Bet: custom amount FSM for games."""

from aiogram import Router

from bot.handlers.bet.custom import router as custom_router

router = Router(name="bet")
router.include_router(custom_router)

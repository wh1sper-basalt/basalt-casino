"""Payments: deposit, withdraw, status."""

from aiogram import Router

from bot.handlers.payments.deposit import router as deposit_router
from bot.handlers.payments.status import router as status_router
from bot.handlers.payments.withdraw import router as withdraw_router

router = Router(name="payments")
router.include_router(deposit_router)
router.include_router(withdraw_router)
router.include_router(status_router)

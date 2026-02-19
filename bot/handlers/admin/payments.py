"""Admin: list pending payment requests, approve/reject. Credit/deduct balance and update user_stats."""

from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery

from bot.config import get_config
from bot.database.queries import payments as payments_queries
from bot.database.queries import user_stats as user_stats_queries
from bot.database.queries import users as users_queries
from bot.handlers.admin.utils import admin_edit_screen
from bot.keyboards.inline import admin_back_to_panel, admin_payment_actions, admin_payments_list_keyboard
from bot.services.balance import credit_deposit, deduct_withdraw
from bot.templates.texts import get_text
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="admin_payments")


@router.callback_query(lambda c: c.data == "admin:payments")
async def cb_admin_payments(callback: CallbackQuery) -> None:
    """Show list of pending requests."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids():
        await callback.answer()
        return
    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "ru"
    pending = await payments_queries.get_pending_requests()
    if not pending:
        text = get_text("admin_no_pending", lang)
        kb = admin_back_to_panel(lang)
    else:
        text = f"{len(pending)} заявок. Выберите для одобрения/отклонения:" if lang == "ru" else f"Pending: {len(pending)}. Select to approve/reject:"
        kb = admin_payments_list_keyboard(pending, lang)
    if callback.message:
        await admin_edit_screen(callback.bot, callback.message.chat.id, callback.message.message_id, text, kb, lang)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("admin:pay:view:"))
async def cb_admin_payment_view(callback: CallbackQuery) -> None:
    """Show one request and Approve/Reject buttons."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids() or not callback.data:
        await callback.answer()
        return
    try:
        request_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer()
        return
    req = await payments_queries.get_payment_request(request_id)
    if not req or req.status != "pending":
        await callback.answer("Request not found or already processed.", show_alert=True)
        return
    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "ru"
    caption = get_text(
        "admin_payment_caption",
        lang,
        id=req.id,
        user_id=req.user_id,
        request_type=req.request_type,
        amount=req.amount,
        created_at=req.created_at,
    )
    kb = admin_payment_actions(request_id, lang)
    if callback.message:
        await admin_edit_screen(callback.bot, callback.message.chat.id, callback.message.message_id, caption, kb, lang)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("admin:pay:approve:"))
async def cb_admin_payment_approve(callback: CallbackQuery) -> None:
    """Approve request: credit/deduct balance, update user_stats, set status."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids() or not callback.data:
        await callback.answer()
        return
    try:
        request_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer()
        return
    req = await payments_queries.get_payment_request(request_id)
    if not req or req.status != "pending":
        await callback.answer("Request not found or already processed.", show_alert=True)
        return
    admin_id = callback.from_user.id
    if req.request_type == "deposit":
        await credit_deposit(req.user_id, req.amount)
        await user_stats_queries.update_stats_after_payment(req.user_id, "deposit", req.amount)
    else:
        await deduct_withdraw(req.user_id, req.amount)
        await user_stats_queries.update_stats_after_payment(req.user_id, "withdraw", req.amount)
    await payments_queries.set_payment_status(request_id, "approved", processed_by=admin_id)
    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "ru"
    pending = await payments_queries.get_pending_requests()
    if not pending:
        text = get_text("admin_no_pending", lang)
        kb = admin_back_to_panel(lang)
    else:
        text = "Одобрено. Заявок: " + str(len(pending)) if lang == "ru" else f"Approved. Pending: {len(pending)}."
        kb = admin_payments_list_keyboard(pending, lang)
    if callback.message:
        await admin_edit_screen(callback.bot, callback.message.chat.id, callback.message.message_id, text, kb, lang)
    await callback.answer("Approved.")


@router.callback_query(lambda c: c.data == "admin:pay:dismiss")
async def cb_admin_payment_dismiss(callback: CallbackQuery) -> None:
    """Dismiss: delete the notification message (e.g. from new request alert in PM)."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids():
        await callback.answer()
        return
    if callback.message:
        try:
            await callback.message.delete()
        except Exception as e:
            log.debug("Could not delete notification message: {}", e)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("admin:pay:reject:"))
async def cb_admin_payment_reject(callback: CallbackQuery) -> None:
    """Reject request: only set status."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids() or not callback.data:
        await callback.answer()
        return
    try:
        request_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer()
        return
    req = await payments_queries.get_payment_request(request_id)
    if not req or req.status != "pending":
        await callback.answer("Request not found or already processed.", show_alert=True)
        return
    admin_id = callback.from_user.id
    await payments_queries.set_payment_status(request_id, "rejected", processed_by=admin_id)
    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "ru"
    pending = await payments_queries.get_pending_requests()
    if not pending:
        text = get_text("admin_no_pending", lang)
        kb = admin_back_to_panel(lang)
    else:
        text = "Отклонено. Заявок: " + str(len(pending)) if lang == "ru" else f"Rejected. Pending: {len(pending)}."
        kb = admin_payments_list_keyboard(pending, lang)
    if callback.message:
        await admin_edit_screen(callback.bot, callback.message.chat.id, callback.message.message_id, text, kb, lang)
    await callback.answer("Rejected.")

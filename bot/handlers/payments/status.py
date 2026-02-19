"""Payment status: list user's requests (pending / approved / rejected)."""

from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery

from bot.database.queries import payments as payments_queries
from bot.database.queries import users as users_queries
from bot.keyboards.inline import payment_status_keyboard
from bot.templates.texts import get_text
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="payment_status")


def _status_display(status: str, lang: str) -> str:
    """Localize status for display."""
    key = f"status_{status}"
    out = get_text(key, lang)
    if out == key:
        return status
    return out


@router.callback_query(lambda c: c.data == "menu:payment_status")
async def cb_payment_status(callback: CallbackQuery) -> None:
    """Show list of user's payment requests (deposit/withdraw, status)."""
    if not callback.from_user or not callback.message:
        return
    user_id = callback.from_user.id
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"
    requests_list = await payments_queries.get_requests_by_user(user_id)
    caption = get_text("payment_status_caption", lang)
    if requests_list:
        lines = []
        for r in requests_list:
            status_str = _status_display(r.status, lang)
            lines.append(
                get_text(
                    "payment_status_item",
                    lang,
                    id=r.id,
                    request_type=r.request_type,
                    amount=r.amount,
                    status=status_str,
                )
            )
        caption = caption + "\n\n" + "\n".join(lines)
    else:
        caption = get_text("payment_status_empty", lang)
    kb = payment_status_keyboard(lang)
    try:
        if callback.message.photo:
            await callback.message.edit_caption(caption=caption, reply_markup=kb)
        else:
            await callback.message.edit_text(caption, reply_markup=kb)
    except Exception:
        await callback.message.answer(caption, reply_markup=kb)
    await callback.answer()

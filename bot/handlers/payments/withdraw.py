"""Withdraw: amount selection (presets + custom FSM), create request. Only in real mode."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Message

from bot.database.queries import payments as payments_queries
from bot.database.queries import settings as settings_queries
from bot.database.queries import users as users_queries
from bot.keyboards.inline import deposit_menu, withdraw_amounts, withdraw_confirm_amount
from bot.services.notify_admin import notify_admins_new_payment_request
from bot.templates.texts import get_text
from bot.utils.currency import format_currency_rub, format_currency_usd, get_usd_rate
from bot.utils.helpers import get_image_path
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="withdraw")


class WithdrawStates(StatesGroup):
    waiting_amount = State()


def _presets_from_settings(settings: object) -> list[int]:
    """Build presets for withdraw (same logic as deposit)."""
    min_bet = getattr(settings, "min_bet", 100)
    max_bet = getattr(settings, "max_bet", 100000)
    presets = [min_bet]
    for p in (500, 1500, 5000, 10000):
        if min_bet <= p <= max_bet and p not in presets:
            presets.append(p)
    return presets[:5]


async def _edit_or_answer(callback: CallbackQuery, caption: str, kb: object, path: object) -> None:
    if not callback.message:
        return
    try:
        if path.exists() and callback.message.photo:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=FSInputFile(path), caption=caption),
                reply_markup=kb,
            )
        elif callback.message.photo:
            await callback.message.edit_caption(caption=caption, reply_markup=kb)
        else:
            await callback.message.edit_text(caption, reply_markup=kb)
    except Exception:
        if path.exists():
            await callback.message.answer_photo(FSInputFile(path), caption=caption, reply_markup=kb)
        else:
            await callback.message.answer(caption, reply_markup=kb)


@router.callback_query(lambda c: c.data == "menu:withdraw")
async def cb_withdraw(callback: CallbackQuery) -> None:
    """Show withdraw amount selection only if real mode and contact sent; else block."""
    if not callback.from_user:
        return
    user_id = callback.from_user.id
    if not await users_queries.can_create_payment_request(user_id):
        user = await users_queries.get_user(user_id)
        lang = user.language if user else "en"
        await callback.answer(get_text("contact_required_for_request", lang), show_alert=True)
        return
    balance_row = await users_queries.get_user_balance(user_id)
    if balance_row is None or balance_row.demo_mode:
        user = await users_queries.get_user(user_id)
        lang = user.language if user else "en"
        await callback.answer(get_text("withdraw_demo_blocked", lang), show_alert=True)
        return
    settings = await settings_queries.get_settings()
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"
    presets = _presets_from_settings(settings)
    caption = get_text(
        "withdraw_amount_caption",
        lang,
        min_bet=settings.min_bet,
        max_bet=settings.max_bet,
    )
    kb = withdraw_amounts(lang, settings.min_bet, settings.max_bet, presets)
    path = get_image_path("withdraw", lang)
    await _edit_or_answer(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("withdraw:amount:"))
async def cb_withdraw_amount(callback: CallbackQuery) -> None:
    """Amount selected (preset). Show Create request, Back."""
    if not callback.from_user or not callback.data:
        return
    try:
        amount = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer()
        return
    settings = await settings_queries.get_settings()
    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "en"
    if amount < settings.min_bet or amount > settings.max_bet:
        await callback.answer(
            get_text("deposit_custom_invalid", lang, min_bet=settings.min_bet, max_bet=settings.max_bet),
            show_alert=True,
        )
        return
    caption = get_text("withdraw_create_caption", lang, amount=amount)
    kb = withdraw_confirm_amount(lang, amount)
    path = get_image_path("withdraw", lang)
    await _edit_or_answer(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(lambda c: c.data == "withdraw:custom")
async def cb_withdraw_custom(callback: CallbackQuery, state: FSMContext) -> None:
    """Enter FSM: ask for custom withdraw amount."""
    if not callback.from_user:
        return
    await state.set_state(WithdrawStates.waiting_amount)
    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "en"
    settings = await settings_queries.get_settings()
    text = get_text(
        "deposit_custom_prompt",
        lang,
        min_bet=settings.min_bet,
        max_bet=settings.max_bet,
    )
    await callback.message.answer(text)
    await callback.answer()


@router.message(WithdrawStates.waiting_amount, F.text)
async def msg_withdraw_custom_amount(message: Message, state: FSMContext) -> None:
    """Process custom withdraw amount: validate min/max, show create request or error."""
    user_id = message.from_user.id if message.from_user else 0
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"
    settings = await settings_queries.get_settings()
    try:
        amount = int((message.text or "").strip().replace(" ", ""))
    except ValueError:
        await message.answer(
            get_text("deposit_custom_invalid", lang, min_bet=settings.min_bet, max_bet=settings.max_bet),
        )
        return
    if amount < settings.min_bet or amount > settings.max_bet:
        await message.answer(
            get_text("deposit_custom_invalid", lang, min_bet=settings.min_bet, max_bet=settings.max_bet),
        )
        return
    await state.clear()
    caption = get_text("withdraw_create_caption", lang, amount=amount)
    kb = withdraw_confirm_amount(lang, amount)
    await message.answer(caption, reply_markup=kb)


@router.callback_query(lambda c: c.data and c.data.startswith("withdraw:create:"))
async def cb_withdraw_create(callback: CallbackQuery) -> None:
    """Create withdraw request (status pending), show confirmation. Requires contact sent first."""
    if not callback.from_user or not callback.data:
        return
    try:
        amount = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer()
        return
    user_id = callback.from_user.id
    if not await users_queries.can_create_payment_request(user_id):
        user = await users_queries.get_user(user_id)
        lang = user.language if user else "en"
        await callback.answer(get_text("contact_required_for_request", lang), show_alert=True)
        return
    balance_row = await users_queries.get_user_balance(user_id)
    if balance_row is None or balance_row.demo_mode:
        user = await users_queries.get_user(user_id)
        lang = user.language if user else "en"
        await callback.answer(get_text("withdraw_demo_blocked", lang), show_alert=True)
        return
    settings = await settings_queries.get_settings()
    if amount < settings.min_bet or amount > settings.max_bet:
        await callback.answer()
        return
    if balance_row.real_balance < amount:
        user = await users_queries.get_user(user_id)
        lang = user.language if user else "en"
        await callback.answer(get_text("withdraw_insufficient_balance", lang), show_alert=True)
        return
    request_id = await payments_queries.create_payment_request(
        user_id=user_id,
        request_type="withdraw",
        amount=amount,
    )
    req = await payments_queries.get_payment_request(request_id)
    if req:
        await notify_admins_new_payment_request(
            callback.bot,
            request_id=req.id,
            request_type="withdraw",
            amount=req.amount,
            user_id=req.user_id,
            created_at=req.created_at,
        )
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"
    caption = get_text("withdraw_request_created", lang, request_id=request_id, amount=amount)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("btn_change_amount", lang), callback_data="withdraw:change")],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="withdraw:cancel")],
        ]
    )
    path = get_image_path("withdraw", lang)
    await _edit_or_answer(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(lambda c: c.data == "withdraw:change")
async def cb_withdraw_change(callback: CallbackQuery, state: FSMContext) -> None:
    """Change amount: go back to amount selection screen."""
    await state.clear()
    if not callback.from_user:
        return
    user_id = callback.from_user.id
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"
    settings = await settings_queries.get_settings()
    presets = _presets_from_settings(settings)
    caption = get_text(
        "withdraw_amount_caption",
        lang,
        min_bet=settings.min_bet,
        max_bet=settings.max_bet,
    )
    kb = withdraw_amounts(lang, settings.min_bet, settings.max_bet, presets)
    path = get_image_path("withdraw", lang)
    await _edit_or_answer(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(lambda c: c.data == "withdraw:cancel")
async def cb_withdraw_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Cancel: clear FSM if any, return to deposit menu (not account) with updated balance."""
    await state.clear()
    if not callback.from_user or not callback.message:
        return
    user_id = callback.from_user.id
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"
    has_contact = users_queries.user_has_contact_sent(user)

    # Получаем актуальный баланс
    balance_row = await users_queries.get_user_balance(user_id)
    if balance_row.demo_mode:
        current_balance = balance_row.demo_balance
        mode_text = "DEMO"
    else:
        current_balance = balance_row.real_balance
        mode_text = "Real"

    if lang == "en":
        usd_rate = await get_usd_rate()
        usd_amount = format_currency_usd(current_balance, usd_rate)
        rub_amount = format_currency_rub(current_balance)
        balance_text = f"{usd_amount} ({rub_amount})"
    else:
        balance_text = format_currency_rub(current_balance)

    caption = get_text("deposit_caption", lang, balance=balance_text, mode=mode_text)
    kb = deposit_menu(lang, has_contact_sent=has_contact)
    path = get_image_path("deposit", lang)
    await _edit_or_answer(callback, caption, kb, path)
    await callback.answer()

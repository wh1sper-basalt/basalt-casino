"""FSM for custom bet amount in games. Callback game:GID:o:OID:custom."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.core.games import GAME_LIST
from bot.database.queries import settings as settings_queries
from bot.database.queries import users as users_queries
from bot.keyboards.inline import confirm_bet
from bot.services.game import calculate_win_amount, get_game_info, get_probability
from bot.templates.texts import get_text
from bot.utils.helpers import get_image_path
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="bet_custom")


class BetAmountStates(StatesGroup):
    waiting_amount = State()


@router.callback_query(lambda c: c.data and ":custom" in c.data and c.data.startswith("game:"))
async def cb_game_custom_amount(callback: CallbackQuery, state: FSMContext) -> None:
    """Enter FSM for custom bet amount. callback_data = game:GID:o:OID:custom."""
    if not callback.data or not callback.from_user:
        return
    parts = callback.data.split(":")
    if len(parts) != 5 or parts[4] != "custom":
        return
    try:
        game_id = int(parts[1])
        outcome_index = int(parts[3])
    except ValueError:
        return
    if game_id not in GAME_LIST:
        return
    info = get_game_info(game_id)
    if outcome_index < 0 or outcome_index >= len(info["outcomes"]):
        return
    await state.set_state(BetAmountStates.waiting_amount)
    await state.update_data(game_id=game_id, outcome_index=outcome_index)
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


@router.message(BetAmountStates.waiting_amount, F.text)
async def msg_bet_amount(message: Message, state: FSMContext) -> None:
    """Process custom amount: validate min/max, show confirm."""
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
    data = await state.get_data()
    game_id = data.get("game_id")
    outcome_index = data.get("outcome_index")
    await state.clear()
    if game_id is None or outcome_index is None or game_id not in GAME_LIST:
        await message.answer(get_text("btn_cancel", lang))
        return
    info = get_game_info(game_id)
    if outcome_index < 0 or outcome_index >= len(info["outcomes"]):
        return
    outcome_name = info["outcomes"][outcome_index]
    ratio = info["ratios"][outcome_index]
    prob = get_probability(game_id, outcome_index)
    potential = calculate_win_amount(amount, float(ratio))
    caption = get_text(
        "confirm_bet_text",
        lang,
        game_name=info["name"],
        outcome=outcome_name,
        amount=amount,
        ratio=ratio,
        prob=prob,
        potential=potential,
    )
    kb = confirm_bet(lang, game_id, outcome_index, amount)
    path = get_image_path("confirm", lang)
    try:
        if path.exists():
            await message.answer_photo(FSInputFile(str(path)), caption=caption, reply_markup=kb)
        else:
            await message.answer(caption, reply_markup=kb)
    except Exception as e:
        log.warning("Confirm photo send failed, fallback to text: {}", e)
        await message.answer(caption, reply_markup=kb)

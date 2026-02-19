"""Game flow: description, outcomes, amount, confirm, place_bet, result."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from bot.core.games import GAME_ID_TO_EMOJI, GAME_ID_TO_IMAGE_SCREEN, GAME_LIST
from bot.database.queries import games as games_queries
from bot.database.queries import settings as settings_queries
from bot.database.queries import user_stats as user_stats_queries
from bot.database.queries import users as users_queries
from bot.keyboards.inline import confirm_bet, game_bet_amounts, game_description_keyboard, game_outcomes, game_result_actions, main_menu
from bot.services.balance import check_sufficient, credit_win, deduct_bet
from bot.services.game import calculate_win_amount, get_game_info, get_probability, resolve_outcome
from bot.templates.texts import get_text
from bot.utils.currency import format_currency_rub, format_currency_usd
from bot.utils.helpers import get_image_path
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="games_flow")

# Double-tap protection: (chat_id, message_id) of confirmation messages already processed
_played_confirm_ids: Set[Tuple[int, int]] = set()

# Exit cleanup: (chat_id, result_message_id) -> (confirm_msg_id, dice_msg_ids) for reliable delete
_exit_cleanup_cache: Dict[Tuple[int, int], Tuple[int, List[int]]] = {}

# Telegram dice emoji characters
_DICE_EMOJI: dict[str, str] = {
    "dice": "🎲",
    "darts": "🎯",
    "basketball": "🏀",
    "football": "⚽",
    "bowling": "🎳",
    "slot_machine": "🎰",
}


def _presets_for_bet(min_bet: int, max_bet: int) -> list[int]:
    """Presets: min_bet, min_bet*2, *5, *10, *20 (capped by max_bet)."""
    presets = [min_bet]
    for m in (2, 5, 10, 20):
        p = min_bet * m
        if p <= max_bet and p not in presets:
            presets.append(p)
    return presets[:5]


async def _edit_or_send(callback: CallbackQuery, caption: str, kb, path, use_photo: bool = True) -> None:
    if not callback.message:
        return
    path_str = str(path) if path else None
    try:
        if use_photo and path and path.exists() and callback.message.photo:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=FSInputFile(path_str), caption=caption),
                reply_markup=kb,
            )
        elif callback.message.photo:
            await callback.message.edit_caption(caption=caption, reply_markup=kb)
        else:
            await callback.message.edit_text(caption, reply_markup=kb)
    except Exception:
        if use_photo and path and path.exists():
            await callback.message.answer_photo(FSInputFile(path_str), caption=caption, reply_markup=kb)
        else:
            await callback.message.answer(caption, reply_markup=kb)


def _format_balance_display(amount: int, lang: str, usd_rate: Optional[float] = None) -> str:
    """Format balance display according to language."""
    if lang == "en" and usd_rate:
        # English: Show USD with RUB in parentheses
        usd_amount = format_currency_usd(amount, usd_rate)
        rub_amount = format_currency_rub(amount)
        return f"{usd_amount} ({rub_amount})"
    # Russian: Just show RUB
    return format_currency_rub(amount)


def _format_button_amount(amount: int, lang: str, usd_rate: Optional[float] = None) -> str:
    """Format button text for bet amounts."""
    if lang == "en" and usd_rate:
        # English: Show USD with RUB in parentheses
        usd_amount = format_currency_usd(amount, usd_rate)
        rub_amount = format_currency_rub(amount)
        return f"{usd_amount} ({rub_amount})"
    # Russian: Just show RUB
    return format_currency_rub(amount)


def _format_amount_text(amount: int, lang: str, usd_rate: Optional[float] = None) -> str:
    """Format amount in text (without parentheses for English)."""
    if lang == "en" and usd_rate:
        # English: Show USD (RUB will be shown elsewhere)
        return format_currency_usd(amount, usd_rate)
    # Russian: Just show RUB
    return format_currency_rub(amount)


@router.callback_query(lambda c: c.data and c.data.startswith("game:") and c.data.count(":") == 2 and c.data.endswith(":bet"))
async def cb_game_description(callback: CallbackQuery) -> None:
    """Show game description + Make bet, Cancel."""
    if not callback.data or not callback.from_user:
        return
    parts = callback.data.split(":")
    if len(parts) != 3:
        return
    try:
        game_id = int(parts[1])
    except ValueError:
        return
    if game_id not in GAME_LIST:
        await callback.answer()
        return

    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "en"
    info = get_game_info(game_id, lang)
    name = info["name"]
    outcomes = info["outcomes"]
    ratios = info.get("ratios", [])

    # Format outcomes and ratios with language
    outcome_texts = []
    for i, outcome in enumerate(outcomes):
        if i < len(ratios):
            outcome_texts.append(f"• {outcome} (x{ratios[i]})")
        else:
            outcome_texts.append(f"• {outcome}")

    caption = get_text("game_description", lang, name=name, outcomes="\n".join(outcome_texts))
    kb = game_description_keyboard(lang, game_id)
    screen = GAME_ID_TO_IMAGE_SCREEN.get(game_id, "gamelist")
    path = get_image_path(screen, lang)
    await _edit_or_send(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("game:") and ":outcomes" in c.data)
async def cb_game_outcomes(callback: CallbackQuery) -> None:
    """Show outcome selection for game."""
    if not callback.data or not callback.from_user:
        return
    parts = callback.data.split(":")
    if len(parts) != 3:
        return
    try:
        game_id = int(parts[1])
    except ValueError:
        return
    if game_id not in GAME_LIST:
        return
    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "en"
    info = get_game_info(game_id, lang)
    caption = get_text("game_choose_outcome", lang)

    # Get ratios for outcomes
    ratios = info.get("ratios", [])
    outcomes_with_ratios = []
    for i, outcome in enumerate(info["outcomes"]):
        if i < len(ratios):
            outcomes_with_ratios.append(f"{outcome} (x{ratios[i]})")
        else:
            outcomes_with_ratios.append(outcome)

    kb = game_outcomes(lang, game_id, outcomes_with_ratios)
    screen = GAME_ID_TO_IMAGE_SCREEN.get(game_id, "gamelist")
    path = get_image_path(screen, lang)
    await _edit_or_send(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("game:") and ":o:" in c.data and ":a:" not in c.data and ":place" not in c.data and ":custom" not in c.data)
async def cb_game_amount(callback: CallbackQuery, **kwargs) -> None:
    """Show amount selection: game:GID:o:OID (no :a: or :place:)."""
    if not callback.data or not callback.from_user:
        return
    parts = callback.data.split(":")
    if len(parts) != 4 or parts[2] != "o":
        return
    try:
        game_id = int(parts[1])
        outcome_index = int(parts[3])
    except ValueError:
        return
    if game_id not in GAME_LIST:
        return
    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "en"
    info = get_game_info(game_id, lang)
    if outcome_index < 0 or outcome_index >= len(info["outcomes"]):
        return
    settings = await settings_queries.get_settings()
    balance_row = await users_queries.get_user_balance(callback.from_user.id)
    balance = 0
    demo_note = ""
    if balance_row:
        balance = balance_row.demo_balance if balance_row.demo_mode else balance_row.real_balance
        if balance_row.demo_mode:
            demo_note = get_text("game_choose_amount_demo_note", lang)

    # Get USD rate from middleware
    usd_rate = kwargs.get("usd_rate")
    if usd_rate is None and lang == "en":
        # Fallback: get rate directly
        from bot.utils.currency import get_usd_rate

        usd_rate = await get_usd_rate()
        log.info(f"Fetched USD rate directly: {usd_rate}")

    # Format balance for display
    balance_text = _format_balance_display(balance, lang, usd_rate)

    # Add note about currency for English users
    currency_note = ""
    if lang == "en":
        currency_note = get_text("game_currency_note", lang)

    presets = _presets_for_bet(settings.min_bet, settings.max_bet)

    # Format preset buttons with language
    preset_buttons = []
    for p in presets:
        preset_buttons.append(_format_button_amount(p, lang, usd_rate))

    caption = get_text(
        "game_choose_amount",
        lang,
        balance=balance_text,
        demo_note=demo_note,
        currency_note=currency_note,
    )

    kb = game_bet_amounts(lang, game_id, outcome_index, settings.min_bet, presets, preset_buttons=preset_buttons)

    screen = GAME_ID_TO_IMAGE_SCREEN.get(game_id, "gamelist")
    path = get_image_path(screen, lang)
    await _edit_or_send(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("game:") and ":o:" in c.data and ":a:" in c.data and ":place" not in c.data)
async def cb_game_confirm(callback: CallbackQuery, **kwargs) -> None:
    """Show confirm: game:GID:o:OID:a:AMT."""
    if not callback.data or not callback.from_user:
        return
    parts = callback.data.split(":")
    if len(parts) != 6 or parts[2] != "o" or parts[4] != "a":
        return
    try:
        game_id = int(parts[1])
        outcome_index = int(parts[3])
        amount = int(parts[5])
    except ValueError:
        return
    if game_id not in GAME_LIST:
        return
    settings = await settings_queries.get_settings()
    if amount < settings.min_bet or amount > settings.max_bet:
        await callback.answer()
        return
    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "en"
    info = get_game_info(game_id, lang)
    if outcome_index < 0 or outcome_index >= len(info["outcomes"]):
        return
    outcome_name = info["outcomes"][outcome_index]
    ratio = info["ratios"][outcome_index]
    prob = get_probability(game_id, outcome_index)
    potential = calculate_win_amount(amount, float(ratio))

    # Get current balance
    balance_row = await users_queries.get_user_balance(callback.from_user.id)
    current_balance = 0
    if balance_row:
        current_balance = balance_row.demo_balance if balance_row.demo_mode else balance_row.real_balance

    potential_balance = current_balance + potential

    # Get USD rate from middleware
    usd_rate = kwargs.get("usd_rate")

    # Format amounts with language
    current_text = _format_balance_display(current_balance, lang, usd_rate)
    potential_text = _format_balance_display(potential_balance, lang, usd_rate)
    potential_win_text = _format_amount_text(potential, lang, usd_rate)
    amount_text = _format_amount_text(amount, lang, usd_rate)

    # Add note about currency for English users
    currency_note = ""
    if lang == "en":
        currency_note = get_text("game_currency_note", lang)

    caption = get_text(
        "confirm_bet_text",
        lang,
        game_name=info["name"],
        outcome=outcome_name,
        amount=amount_text,
        ratio=ratio,
        prob=prob,
        potential=potential_win_text,
        current_balance=current_text,
        potential_balance=potential_text,
        currency_note=currency_note,
    )
    kb = confirm_bet(lang, game_id, outcome_index, amount)
    path = get_image_path("confirm", lang)

    await _edit_or_send(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("game:") and ":place:" in c.data)
async def cb_game_place(callback: CallbackQuery, state: FSMContext) -> None:
    """Execute bet: deduct, send dice, resolve, credit, save, result. Double-tap protection."""
    if not callback.data or not callback.from_user or not callback.message:
        return
    parts = callback.data.split(":")
    if len(parts) != 6 or parts[4] != "place":
        return
    try:
        game_id = int(parts[1])
        outcome_index = int(parts[3])
        amount = int(parts[5])
    except ValueError:
        return
    user_id = callback.from_user.id
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"
    chat_id = callback.message.chat.id
    msg_id = callback.message.message_id
    key = (chat_id, msg_id)
    if key in _played_confirm_ids:
        await callback.answer(get_text("game_already_played", lang), show_alert=True)
        return
    _played_confirm_ids.add(key)
    balance_row = await users_queries.get_user_balance(user_id)
    if not balance_row:
        _played_confirm_ids.discard(key)
        await callback.answer(get_text("game_bet_insufficient", lang), show_alert=True)
        return
    is_demo = bool(balance_row.demo_mode)
    sufficient = await check_sufficient(user_id, amount, is_demo)
    if not sufficient:
        _played_confirm_ids.discard(key)
        await callback.answer(get_text("game_bet_insufficient", lang), show_alert=True)
        return

    await deduct_bet(user_id, amount, is_demo)
    game_type = GAME_ID_TO_EMOJI.get(game_id, "dice")
    emoji_char = _DICE_EMOJI.get(game_type, "🎲")
    bot = callback.bot
    fast_mode = bool(user.fast_mode) if user else False

    if game_id == 1:
        dice1 = await bot.send_dice(chat_id=chat_id, emoji=emoji_char, reply_to_message_id=msg_id)
        dice2 = await bot.send_dice(chat_id=chat_id, emoji=emoji_char, reply_to_message_id=msg_id)
        if not fast_mode:
            await asyncio.sleep(3)
        v1 = dice1.dice.value if dice1.dice else 1
        v2 = dice2.dice.value if dice2.dice else 1
        dice_values = [v1, v2]
        dice_msg_ids = [dice1.message_id, dice2.message_id]
    else:
        dice_msg = await bot.send_dice(chat_id=chat_id, emoji=emoji_char, reply_to_message_id=msg_id)
        if not fast_mode:
            await asyncio.sleep(3)
        val = dice_msg.dice.value if dice_msg.dice else 0
        dice_values = val
        dice_msg_ids = [dice_msg.message_id]
    is_win, outcome_name, ratio = resolve_outcome(game_id, outcome_index, dice_values)
    win_amount = calculate_win_amount(amount, ratio) if is_win else 0
    if is_win:
        await credit_win(user_id, win_amount, is_demo)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    await games_queries.save_game(
        user_id=user_id,
        game_type=game_type,
        game_id=game_id,
        bet_amount=amount,
        outcome=outcome_name,
        is_win=is_win,
        win_amount=win_amount,
        is_demo=is_demo,
        played_at=now,
    )
    await user_stats_queries.update_stats_after_game(user_id, is_win, amount, win_amount)

    await state.update_data(
        game_exit_confirm_chat_id=chat_id,
        game_exit_confirm_msg_id=msg_id,
        game_exit_dice_msg_ids=dice_msg_ids,
    )

    if is_win:
        if lang == "en":
            usd_rate = None
            if hasattr(callback, "kwargs") and "usd_rate" in callback.kwargs:
                usd_rate = callback.kwargs.get("usd_rate")
            if usd_rate is None:
                from bot.utils.currency import get_usd_rate

                usd_rate = await get_usd_rate()
            usd_amount = format_currency_usd(win_amount, usd_rate)
            rub_amount = format_currency_rub(win_amount)
            win_text = f"{usd_amount} ({rub_amount})"
            result_caption = get_text("win_message", lang, amount=win_text)
        else:
            result_caption = get_text("win_message", lang, amount=win_amount)
    else:
        result_caption = get_text("lost_message", lang)

    screen = "win" if is_win else "loss"
    path = get_image_path(screen, lang)
    if not is_win and not path.exists():
        path = get_image_path("lost", lang)
    kb = game_result_actions(
        lang,
        game_id,
        outcome_index,
        amount,
        confirm_msg_id=msg_id,
        dice_msg_ids=dice_msg_ids,
    )
    try:
        if path.exists():
            sent = await callback.message.answer_photo(FSInputFile(str(path)), caption=result_caption, reply_markup=kb)
        else:
            sent = await callback.message.answer(result_caption, reply_markup=kb)
        _exit_cleanup_cache[(chat_id, sent.message_id)] = (msg_id, list(dice_msg_ids))
    except Exception as e:
        log.warning("Result photo send failed ({}), fallback to text: {}", path, e)
        sent = await callback.message.answer(result_caption, reply_markup=kb)
        _exit_cleanup_cache[(chat_id, sent.message_id)] = (msg_id, list(dice_msg_ids))
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("game:repeat:"))
async def cb_game_repeat(callback: CallbackQuery, state: FSMContext, **kwargs) -> None:
    """Repeat: delete previous confirm and dice messages, then show confirm again with same params."""
    if not callback.data or not callback.from_user or not callback.message:
        return
    chat_id = callback.message.chat.id
    bot = callback.bot
    data = await state.get_data()
    prev_confirm_id = data.get("game_exit_confirm_msg_id")
    raw_dice = data.get("game_exit_dice_msg_ids")
    prev_dice_ids = list(raw_dice) if isinstance(raw_dice, (list, tuple)) else []
    await state.clear()
    if prev_confirm_id is not None:
        try:
            await bot.delete_message(chat_id, prev_confirm_id)
        except Exception as e:
            log.debug("Repeat: could not delete previous confirm: {}", e)
    for mid in prev_dice_ids:
        try:
            await bot.delete_message(chat_id, int(mid))
        except Exception as e:
            log.debug("Repeat: could not delete previous dice msg {}: {}", mid, e)

    parts = callback.data.split(":")
    if len(parts) != 5:
        return
    try:
        game_id = int(parts[2])
        outcome_index = int(parts[3])
        amount = int(parts[4])
    except (ValueError, IndexError):
        await callback.answer()
        return
    if game_id not in GAME_LIST:
        return
    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "en"
    info = get_game_info(game_id, lang)
    if outcome_index < 0 or outcome_index >= len(info["outcomes"]):
        return
    outcome_name = info["outcomes"][outcome_index]
    ratio = info["ratios"][outcome_index]
    prob = get_probability(game_id, outcome_index)
    potential = calculate_win_amount(amount, float(ratio))

    # Get current balance
    balance_row = await users_queries.get_user_balance(callback.from_user.id)
    current_balance = 0
    if balance_row:
        current_balance = balance_row.demo_balance if balance_row.demo_mode else balance_row.real_balance

    potential_balance = current_balance + potential

    # Get USD rate from middleware
    usd_rate = kwargs.get("usd_rate")

    # Format amounts with language
    current_text = _format_balance_display(current_balance, lang, usd_rate)
    potential_text = _format_balance_display(potential_balance, lang, usd_rate)
    potential_win_text = _format_amount_text(potential, lang, usd_rate)
    amount_text = _format_amount_text(amount, lang, usd_rate)

    # Add note about currency for English users
    currency_note = ""
    if lang == "en":
        currency_note = get_text("game_currency_note", lang)

    caption = get_text(
        "confirm_bet_text",
        lang,
        game_name=info["name"],
        outcome=outcome_name,
        amount=amount_text,
        ratio=ratio,
        prob=prob,
        potential=potential_win_text,
        current_balance=current_text,
        potential_balance=potential_text,
        currency_note=currency_note,
    )
    kb = confirm_bet(lang, game_id, outcome_index, amount)
    path = get_image_path("confirm", lang)
    await _edit_or_send(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("game:exit_cleanup"))
async def cb_game_exit_cleanup(callback: CallbackQuery, state: FSMContext) -> None:
    """Delete confirmation message, dice message(s), result message; then send main menu."""
    if not callback.message or not callback.from_user:
        await callback.answer()
        return
    result_chat_id = callback.message.chat.id
    result_msg_id = callback.message.message_id
    bot = callback.bot
    chat_id_use = result_chat_id
    confirm_msg_id = None
    dice_msg_ids: list[int] = []
    cache_key = (result_chat_id, result_msg_id)
    if cache_key in _exit_cleanup_cache:
        confirm_msg_id, dice_msg_ids = _exit_cleanup_cache.pop(cache_key)
    if confirm_msg_id is None or not dice_msg_ids:
        parts = (callback.data or "").split(":")
        if len(parts) >= 4:
            try:
                confirm_msg_id = int(parts[2])
                dice_msg_ids = [int(parts[3])]
                if len(parts) >= 5:
                    dice_msg_ids.append(int(parts[4]))
            except (ValueError, IndexError):
                pass
        if confirm_msg_id is None or not dice_msg_ids:
            data = await state.get_data()
            if confirm_msg_id is None:
                confirm_msg_id = data.get("game_exit_confirm_msg_id")
            if not dice_msg_ids:
                raw = data.get("game_exit_dice_msg_ids")
                dice_msg_ids = list(raw) if isinstance(raw, (list, tuple)) else []
            chat_id_use = data.get("game_exit_confirm_chat_id") or result_chat_id
    await state.clear()
    # Delete in reverse order (newest first); in private chats Telegram allows dice delete only after 24h
    try:
        await callback.message.delete()
    except Exception as e:
        log.debug("Could not delete result message: {}", e)
    await asyncio.sleep(0.05)
    for mid in reversed(dice_msg_ids):
        try:
            await bot.delete_message(chat_id_use, int(mid))
        except Exception as e:
            log.debug("Dice msg {} not deleted (private chat: dice only after 24h): {}", mid, e)
        await asyncio.sleep(0.05)
    if confirm_msg_id is not None:
        try:
            await bot.delete_message(chat_id_use, confirm_msg_id)
        except Exception as e:
            log.debug("Could not delete confirm message: {}", e)

    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "en"
    caption = get_text("welcome_return", lang)
    kb = main_menu(lang)
    path = get_image_path("home", lang)
    try:
        if path.exists():
            await bot.send_photo(result_chat_id, FSInputFile(str(path)), caption=caption, reply_markup=kb)
        else:
            await bot.send_message(result_chat_id, caption, reply_markup=kb)
    except Exception as e:
        log.warning("Send main menu after exit failed: {}", e)
        await bot.send_message(result_chat_id, caption, reply_markup=kb)
    await callback.answer()

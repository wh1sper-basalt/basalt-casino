"""Stats menu: View simple text statistics (8 indicators) with Reset (UI only) and Back buttons."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from bot.database.queries import games as games_queries
from bot.database.queries import user_stats as stats_queries
from bot.database.queries import users as users_queries
from bot.keyboards.inline import stats_menu
from bot.templates.texts import get_text
from bot.utils.helpers import format_amount, get_image_path
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="user_stats")


def _calculate_winrate(wins: int, total: int) -> float:
    """Calculate winrate percentage."""
    if total == 0:
        return 0.0
    return round((wins / total * 100), 2)


def _calculate_avg_bet(total_bet: int, total_games: int) -> int:
    """Calculate average bet amount."""
    if total_games == 0:
        return 0
    return round(total_bet / total_games)


async def _edit_or_answer(callback: CallbackQuery, caption: str, kb, path) -> None:
    """Edit or send new message with photo/text."""
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


@router.callback_query(F.data == "menu:stats")
async def cb_stats(callback: CallbackQuery) -> None:
    """Show simple text statistics with reset and back buttons."""
    if not callback.from_user:
        return

    user_id = callback.from_user.id

    # Get user data
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"

    # Get statistics using the correct function
    stats = await stats_queries.get_user_stats(user_id)

    # Get total bet amount for average calculation using the correct function
    total_bet = await games_queries.get_total_bet_by_user(user_id)

    # Extract values (handle case when stats is None)
    if stats:
        total_games = stats.total_games
        total_wins = stats.total_wins
        total_losses = stats.total_losses
        total_won = stats.total_won
        total_lost = stats.total_lost
    else:
        total_games = 0
        total_wins = 0
        total_losses = 0
        total_won = 0
        total_lost = 0

    # Calculate derived values
    winrate = _calculate_winrate(total_wins, total_games)
    net_profit = total_won - total_lost
    avg_bet = _calculate_avg_bet(total_bet, total_games)

    # Determine sign for net profit
    profit_sign = "+" if net_profit > 0 else ("−" if net_profit < 0 else "")

    # Build caption (8 indicators as plain text)
    caption_lines = [
        "📊 **СТАТИСТИКА**",
        "",
        f"🎮 Всего игр: {total_games}",
        f"✅ Всего побед: {total_wins}",
        f"❌ Всего проигрышей: {total_losses}",
        f"📈 Винрейт: {winrate}%",
        f"💰 Выигрыш на: {format_amount(total_won)}",
        f"💸 Проигрыш на: {format_amount(total_lost)}",
        f"💵 Чистый профит: {profit_sign}{format_amount(abs(net_profit)) if net_profit != 0 else '0'}",
        f"📊 Средняя ставка: {format_amount(avg_bet)}",
    ]

    caption = "\n".join(caption_lines)

    # Get keyboard (Reset and Back only)
    kb = stats_menu(lang)

    # Get image path
    path = get_image_path("stats", lang)

    await _edit_or_answer(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(F.data == "stats:reset")
async def cb_stats_reset(callback: CallbackQuery) -> None:
    """Reset statistics (UI only) - just show success message."""
    if not callback.from_user:
        return

    user_id = callback.from_user.id
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"

    # Just show success message (data stays in DB)
    await callback.answer(text=get_text("stats_reset_success", lang), show_alert=True)

    # Return to stats menu (refresh the stats display)
    # We need to call the stats handler again
    # This is a bit tricky - we can either:
    # Option 1: Edit the message to show stats again
    # Option 2: Let the user click Back and then Stats again

    # For simplicity, we'll just keep them on the same screen
    # and they can refresh by clicking Back and then Stats again

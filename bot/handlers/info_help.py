"""Commands /info and /help: description + Telegraph/support links; delete command message; Close deletes reply."""

from __future__ import annotations

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.config import get_config
from bot.database.queries import users as users_queries
from bot.keyboards.inline import help_buttons, info_buttons
from bot.templates.texts import get_text
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="info_help")


def _telegraph_urls_from_config() -> dict[str, str]:
    """Build dict of Telegraph URLs from config (keys: rules, rules_games, deposit, support, faq)."""
    c = get_config()
    return {
        "rules": getattr(c, "url_telegraph_rules", "") or "#",
        "rules_games": getattr(c, "url_telegraph_games", "") or "#",
        "deposit": getattr(c, "url_telegraph_deposit", "") or "#",
        "support": getattr(c, "url_telegraph_support", "") or "#",
        "faq": getattr(c, "url_telegraph_faq", "") or "#",
    }


async def _get_support_username(bot: Bot) -> str:
    """Get support admin username by support_user_id (e.g. 1251526792); fallback to config or placeholder."""
    config = get_config()
    user_id = getattr(config, "support_user_id", 1251526792)
    try:
        chat = await bot.get_chat(user_id)
        if chat.username:
            return chat.username
    except Exception as e:
        log.debug("Could not get support username for %s: %s", user_id, e)
    return config.support_username.strip() or "Support"


@router.message(Command("info"))
async def cmd_info(message: Message) -> None:
    """Send info caption + Telegraph links (Rules, Game rules, Deposit, Support, FAQ) and Close. Delete command."""
    if not message.from_user:
        return
    user = await users_queries.get_user(message.from_user.id)
    lang = user.language if user else "en"
    caption = get_text("info_caption", lang)
    urls = _telegraph_urls_from_config()
    kb = info_buttons(urls, lang)
    await message.answer(caption, reply_markup=kb)
    try:
        await message.delete()
    except Exception:
        pass


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Send help caption + Write to support (t.me/username?text=...) and Close. Delete command."""
    if not message.from_user:
        return
    user = await users_queries.get_user(message.from_user.id)
    lang = user.language if user else "en"
    caption = get_text("help_caption", lang)
    start_text = get_text("help_start_text", lang)
    username = await _get_support_username(message.bot)
    kb = help_buttons(username, start_text, lang)
    await message.answer(caption, reply_markup=kb)
    try:
        await message.delete()
    except Exception:
        pass


@router.callback_query(lambda c: c.data == "info:close")
async def cb_info_close(callback: CallbackQuery) -> None:
    """Close: delete the info message."""
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
    await callback.answer()


@router.callback_query(lambda c: c.data == "help:close")
async def cb_help_close(callback: CallbackQuery) -> None:
    """Close: delete the help message."""
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
    await callback.answer()

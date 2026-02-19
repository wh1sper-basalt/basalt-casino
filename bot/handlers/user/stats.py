"""Stats menu: View statistics (WebApp or fallback Flet subprocess), Back."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from aiogram import Router
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from bot.config import get_config
from bot.database.queries import users as users_queries
from bot.keyboards.inline import stats_menu
from bot.templates.texts import get_text
from bot.utils.helpers import get_image_path
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="user_stats")


def _webapp_url(user_id: int) -> str | None:
    """Build WebApp URL with user_id if base URL is set."""
    base = (get_config().webapp_base_url or "").strip().rstrip("/")
    if not base:
        return None
    return f"{base}?user_id={user_id}"


def _flet_app_path() -> Path:
    """Path to flet_webapp (or flet_app) main.py (project root = parent of bot)."""
    root = Path(__file__).resolve().parent.parent.parent
    for name in ("flet_webapp", "flet_app"):
        p = root / name / "main.py"
        if p.exists():
            return p
    return root / "flet_app" / "main.py"


async def _edit_or_answer(callback: CallbackQuery, caption: str, kb, path) -> None:
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


@router.callback_query(lambda c: c.data == "menu:stats")
async def cb_stats(callback: CallbackQuery) -> None:
    """Show stats menu: View statistics (WebApp or callback), Back."""
    if not callback.from_user:
        return
    user_id = callback.from_user.id
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"
    caption = get_text("stats_caption", lang)
    webapp_url = _webapp_url(user_id)
    kb = stats_menu(lang, webapp_url=webapp_url)
    path = get_image_path("stats", lang)
    await _edit_or_answer(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(lambda c: c.data == "stats:view")
async def cb_stats_view(callback: CallbackQuery) -> None:
    """Fallback when WebApp URL not set: launch Flet app in subprocess (same machine)."""
    if not callback.from_user:
        return
    user_id = callback.from_user.id
    flet_path = _flet_app_path()
    if not flet_path.exists():
        await callback.answer("Статистика временно недоступна.", show_alert=True)
        return
    try:
        subprocess.Popen(
            [sys.executable, str(flet_path), str(user_id)],
            cwd=str(flet_path.parent.parent),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        log.warning("Failed to start Flet stats app: %s", e)
        await callback.answer("Не удалось открыть приложение статистики.", show_alert=True)
        return
    await callback.answer("📊 Статистика открывается...", show_alert=False)

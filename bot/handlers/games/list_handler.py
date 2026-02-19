"""Games list: menu:play, game:list."""

from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from bot.database.queries import users as users_queries
from bot.keyboards.inline import games_list
from bot.templates.texts import get_text
from bot.utils.helpers import get_image_path
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="games_list")


async def _edit_or_send(callback: CallbackQuery, caption: str, kb, path, use_photo: bool = True) -> None:
    if not callback.message:
        return
    try:
        if use_photo and path.exists() and callback.message.photo:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=FSInputFile(path), caption=caption),
                reply_markup=kb,
            )
        elif callback.message.photo:
            await callback.message.edit_caption(caption=caption, reply_markup=kb)
        else:
            await callback.message.edit_text(caption, reply_markup=kb)
    except Exception:
        if use_photo and path.exists():
            await callback.message.answer_photo(FSInputFile(path), caption=caption, reply_markup=kb)
        else:
            await callback.message.answer(caption, reply_markup=kb)


@router.callback_query(lambda c: c.data == "menu:play")
@router.callback_query(lambda c: c.data == "game:list")
async def cb_games_list(callback: CallbackQuery) -> None:
    """Show games list (8 games + Back)."""
    if not callback.from_user:
        return
    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "en"
    caption = get_text("games_list_caption", lang)
    kb = games_list(lang)
    path = get_image_path("gamelist", lang)
    await _edit_or_send(callback, caption, kb, path)
    await callback.answer()

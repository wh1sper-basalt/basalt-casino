"""Admin panel: always edit the same message (image + caption + keyboard), never send new messages."""

from __future__ import annotations

from pathlib import Path

from aiogram.types import FSInputFile, InputMediaPhoto

from bot.utils.helpers import get_image_path


def get_admin_panel_path(lang: str) -> Path:
    """Path to basalt_adminpanel.png (or .jpg) for the given lang."""
    path = get_image_path("adminpanel", lang)
    if path.exists():
        return path
    return get_image_path("adminpanel", "en")


async def admin_edit_screen(bot, chat_id: int, message_id: int, caption: str, reply_markup, lang: str) -> bool:
    """
    Edit the admin panel message: same image (basalt_adminpanel) + new caption + new keyboard.
    Returns True if edited successfully. Use this for all admin callback navigation so the chat stays clean.
    """
    path = get_admin_panel_path(lang)
    try:
        if path.exists():
            await bot.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=InputMediaPhoto(media=FSInputFile(str(path)), caption=caption),
                reply_markup=reply_markup,
            )
        else:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=caption,
                reply_markup=reply_markup,
            )
        return True
    except Exception:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=caption,
                reply_markup=reply_markup,
            )
            return True
        except Exception:
            return False

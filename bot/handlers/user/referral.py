"""Referral info screen: show referral link and share button."""

from __future__ import annotations

from urllib.parse import quote

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from bot.database.queries import settings as settings_queries
from bot.database.queries import users as users_queries
from bot.keyboards.inline import referral_menu
from bot.templates.texts import get_text
from bot.utils.helpers import get_image_path
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="user_referral")


@router.callback_query(F.data == "menu:referral")
async def cb_referral(callback: CallbackQuery) -> None:
    """Show referral screen with link and share button."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"

    settings = await settings_queries.get_settings()
    bonus = settings.referral_bonus

    # Get bot username
    bot_me = await callback.bot.me()
    bot_username = bot_me.username

    # Get or generate referral link
    referral_code = user.referral_link
    if not referral_code:
        # If somehow missing, generate now
        from bot.services.referral import generate_referral_link

        referral_code = generate_referral_link(user_id, bot_username)
        await users_queries.update_user(user_id, referral_link=referral_code)

    # Build full referral link
    full_link = f"https://t.me/{bot_username}?start={referral_code}"

    # Text for sharing
    share_text = get_text("referral_share_text", lang)

    # Build caption
    caption = get_text("referral_caption", lang, link=full_link, share_text=quote(share_text), bonus=bonus)

    # Get keyboard (Share and Back)
    kb = referral_menu(lang, full_link, share_text)

    # Get image
    path = get_image_path("referral", lang)

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

    await callback.answer()

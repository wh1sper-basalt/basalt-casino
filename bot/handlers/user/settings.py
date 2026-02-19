"""Settings: Notifications, FAST MODE; Mode switch; Language RU/EN."""

from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from bot.database.queries import users as users_queries
from bot.keyboards.inline import account_menu, language_switch, mode_switch, settings_menu
from bot.templates.texts import get_text
from bot.utils.helpers import get_image_path
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="user_settings")


async def _edit_or_answer(callback: CallbackQuery, caption: str, kb, path) -> None:
    """Edit message to caption+keyboard, or send new photo if path exists."""
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


@router.callback_query(lambda c: c.data == "menu:settings")
async def cb_settings(callback: CallbackQuery) -> None:
    """Show settings: Notifications, FAST MODE, Back."""
    if not callback.from_user:
        return
    user_id = callback.from_user.id
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"
    notif = bool(user.notifications_enabled) if user else True
    fast = bool(user.fast_mode) if user else False
    caption = get_text("settings_caption", lang)
    kb = settings_menu(lang, notif, fast)
    path = get_image_path("settings", lang)
    await _edit_or_answer(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(lambda c: c.data == "settings:notif")
async def cb_toggle_notif(callback: CallbackQuery) -> None:
    """Toggle notifications_enabled and refresh settings screen."""
    if not callback.from_user:
        return
    user_id = callback.from_user.id
    user = await users_queries.get_user(user_id)
    if user:
        new_val = not user.notifications_enabled
        await users_queries.set_notifications(user_id, new_val)
    lang = user.language if user else "en"
    user = await users_queries.get_user(user_id)
    notif = bool(user.notifications_enabled) if user else True
    fast = bool(user.fast_mode) if user else False
    caption = get_text("settings_caption", lang)
    kb = settings_menu(lang, notif, fast)
    path = get_image_path("settings", lang)
    await _edit_or_answer(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(lambda c: c.data == "settings:fast")
async def cb_toggle_fast(callback: CallbackQuery) -> None:
    """Toggle fast_mode and refresh settings screen."""
    if not callback.from_user:
        return
    user_id = callback.from_user.id
    user = await users_queries.get_user(user_id)
    if user:
        new_val = not user.fast_mode
        await users_queries.set_fast_mode(user_id, new_val)
    lang = user.language if user else "en"
    user = await users_queries.get_user(user_id)
    notif = bool(user.notifications_enabled) if user else True
    fast = bool(user.fast_mode) if user else False
    caption = get_text("settings_caption", lang)
    kb = settings_menu(lang, notif, fast)
    path = get_image_path("settings", lang)
    await _edit_or_answer(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:mode")
async def cb_mode(callback: CallbackQuery) -> None:
    """Show mode screen: current mode (Demo/Real), switch button, Back."""
    if not callback.from_user:
        return
    user_id = callback.from_user.id
    balance = await users_queries.get_user_balance(user_id)
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"
    demo = bool(balance.demo_mode) if balance else True
    caption = get_text("mode_caption_demo", lang) if demo else get_text("mode_caption_real", lang)
    kb = mode_switch(lang, demo)
    path = get_image_path("gamemode", lang)
    await _edit_or_answer(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(lambda c: c.data in ("mode:switch_real", "mode:switch_demo"))
async def cb_mode_switch(callback: CallbackQuery) -> None:
    """Switch demo_mode: switch_real -> set demo_mode=0, switch_demo -> set demo_mode=1."""
    if not callback.from_user:
        return
    user_id = callback.from_user.id
    is_switch_real = callback.data == "mode:switch_real"
    await users_queries.update_balance(user_id, demo_mode=1 if not is_switch_real else 0)
    balance = await users_queries.get_user_balance(user_id)
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"
    demo = bool(balance.demo_mode) if balance else True
    caption = get_text("mode_caption_demo", lang) if demo else get_text("mode_caption_real", lang)
    kb = mode_switch(lang, demo)
    path = get_image_path("gamemode", lang)
    await _edit_or_answer(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:language")
async def cb_language(callback: CallbackQuery) -> None:
    """Show language: RU, EN, Back."""
    if not callback.from_user:
        return
    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "en"
    caption = get_text("language_caption", lang)
    kb = language_switch(lang)
    path = get_image_path("language", lang)
    await _edit_or_answer(callback, caption, kb, path)
    await callback.answer()


@router.callback_query(lambda c: c.data in ("lang:ru", "lang:en"))
async def cb_lang_set(callback: CallbackQuery) -> None:
    """Set language and go back to account menu."""
    if not callback.from_user:
        return
    user_id = callback.from_user.id
    new_lang = "ru" if callback.data == "lang:ru" else "en"
    await users_queries.update_user(user_id, language=new_lang)
    caption = get_text("account_caption", new_lang)
    kb = account_menu(new_lang)
    path = get_image_path("account", new_lang)
    await _edit_or_answer(callback, caption, kb, path)
    await callback.answer()

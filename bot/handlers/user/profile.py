"""Account menu: photo + caption + account_menu keyboard; handle Back to main."""

from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from bot.database.queries import users as users_queries
from bot.keyboards.inline import account_menu, main_menu
from bot.services import demo as demo_service
from bot.templates.texts import get_text
from bot.utils.helpers import get_image_path, seconds_to_hours_minutes
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="user_profile")


@router.callback_query(lambda c: c.data == "menu:account")
async def cb_account(callback: CallbackQuery, **kwargs: object) -> None:
    """Show account screen: basalt_account.png (from images/{lang}/), caption, Statistics/Settings/Mode/Deposit[/Withdraw][/Restore demo], Back."""
    if not callback.from_user or not callback.message:
        return
    user_id = callback.from_user.id
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"
    balance_row = await users_queries.get_user_balance(user_id)
    demo_mode = bool(balance_row.demo_mode) if balance_row else True
    need_demo_restore = kwargs.get("need_demo_restore", False)
    caption = get_text("account_caption", lang)
    path = get_image_path("account", lang)
    kb = account_menu(lang, need_demo_restore=need_demo_restore, demo_mode=demo_mode)
    try:
        if path.exists():
            photo = FSInputFile(path)
            if callback.message.photo:
                await callback.message.edit_media(
                    media=InputMediaPhoto(media=photo, caption=caption),
                    reply_markup=kb,
                )
            else:
                await callback.message.edit_text(caption, reply_markup=kb)
        else:
            await callback.message.edit_text(caption, reply_markup=kb)
    except Exception as e:
        log.debug("Edit failed, sending new message: {}", e)
        if path.exists():
            await callback.message.answer_photo(FSInputFile(path), caption=caption, reply_markup=kb)
        else:
            await callback.message.answer(caption, reply_markup=kb)
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:back_main")
async def cb_back_main(callback: CallbackQuery) -> None:
    """Return to main menu (same as after /start but without photo delete)."""
    if not callback.from_user or not callback.message:
        return
    user_id = callback.from_user.id
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"
    caption = get_text("welcome_return", lang)
    kb = main_menu(lang)
    path = get_image_path("home", lang)
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


@router.callback_query(lambda c: c.data == "account:back")
async def cb_back_account(callback: CallbackQuery, **kwargs: object) -> None:
    """Back to account menu (reuse account screen)."""
    if not callback.from_user or not callback.message:
        return
    user_id = callback.from_user.id
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"
    balance_row = await users_queries.get_user_balance(user_id)
    demo_mode = bool(balance_row.demo_mode) if balance_row else True
    need_demo_restore = kwargs.get("need_demo_restore", False)
    caption = get_text("account_caption", lang)
    path = get_image_path("account", lang)
    kb = account_menu(lang, need_demo_restore=need_demo_restore, demo_mode=demo_mode)
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
        await callback.message.answer(caption, reply_markup=kb)
    await callback.answer()


@router.callback_query(lambda c: c.data == "demo:restore")
async def cb_demo_restore(callback: CallbackQuery) -> None:
    """Restore demo balance if allowed (24h cooldown); else show next restore in X hours."""
    if not callback.from_user or not callback.message:
        return
    user_id = callback.from_user.id
    user = await users_queries.get_user(user_id)
    lang = user.language if user else "en"
    allowed, seconds_remaining = await demo_service.can_restore_demo(user_id)
    if allowed:
        await demo_service.perform_demo_restore(user_id)
        caption = get_text("demo_restore_success", lang)
        balance_row = await users_queries.get_user_balance(user_id)
        demo_mode = bool(balance_row.demo_mode) if balance_row else True
        kb = account_menu(lang, need_demo_restore=False, demo_mode=demo_mode)
    else:
        if seconds_remaining > 0:
            caption = get_text("next_restore_in", lang, time_left=seconds_to_hours_minutes(seconds_remaining))
        else:
            caption = get_text("demo_restore_not_needed", lang)
        kb = None
    try:
        if callback.message.photo:
            await callback.message.edit_caption(caption=caption, reply_markup=kb)
        else:
            await callback.message.edit_text(caption, reply_markup=kb)
    except Exception:
        await callback.message.answer(caption, reply_markup=kb)
    await callback.answer()

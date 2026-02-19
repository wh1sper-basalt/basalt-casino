"""Admin panel: /admin command and main menu. Only one message — always edit (image + caption + kb)."""

from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.config import get_config
from bot.database.queries import users as users_queries
from bot.handlers.admin.utils import admin_edit_screen, get_admin_panel_path
from bot.keyboards.inline import admin_main_menu
from bot.templates.texts import get_text
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="admin_panel")


@router.message(lambda m: m.text and m.text.strip() == "/admin")
async def cmd_admin(message: Message) -> None:
    """Show admin panel (single message with photo). Delete /admin message."""
    if not message.from_user:
        return
    config = get_config()
    admin_ids = config.get_admin_ids()
    if message.from_user.id not in admin_ids:
        return
    user = await users_queries.get_user(message.from_user.id)
    lang = user.language if user else "ru"
    caption = get_text("admin_panel_caption", lang)
    kb = admin_main_menu(lang)
    path = get_admin_panel_path(lang)
    if path.exists():
        await message.answer_photo(FSInputFile(str(path)), caption=caption, reply_markup=kb)
    else:
        await message.answer(caption, reply_markup=kb)
    try:
        await message.delete()
    except Exception as e:
        log.debug("Could not delete /admin message: {}", e)


@router.callback_query(lambda c: c.data == "admin:panel")
async def cb_admin_panel(callback: CallbackQuery, state: FSMContext) -> None:
    """Return to admin main menu: edit same message (image + caption + kb)."""
    await state.clear()
    if not callback.message or not callback.from_user:
        return
    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "ru"
    caption = get_text("admin_panel_caption", lang)
    kb = admin_main_menu(lang)
    await admin_edit_screen(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        caption,
        kb,
        lang,
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "admin:exit")
async def cb_admin_exit(callback: CallbackQuery) -> None:
    """Exit admin panel: delete the message."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids():
        await callback.answer()
        return
    if callback.message:
        try:
            await callback.message.delete()
        except Exception as e:
            log.debug("Could not delete admin panel message: {}", e)
    await callback.answer()

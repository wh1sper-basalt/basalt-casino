"""Admin: broadcast to users with notifications_enabled=1. Delay 0.05s; format text + channel link."""

from __future__ import annotations

import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.config import get_config
from bot.database.queries import users as users_queries
from bot.handlers.admin.utils import admin_edit_screen
from bot.keyboards.inline import admin_back_to_panel
from bot.templates.texts import get_text
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="admin_broadcast")


class BroadcastStates(StatesGroup):
    waiting_text = State()


@router.callback_query(lambda c: c.data == "admin:broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Ask for broadcast text (FSM)."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids():
        await callback.answer()
        return
    await state.set_state(BroadcastStates.waiting_text)
    await state.update_data(
        admin_chat_id=callback.message.chat.id if callback.message else None,
        admin_message_id=callback.message.message_id if callback.message else None,
    )
    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "ru"
    text = get_text("admin_broadcast_prompt", lang)
    kb = admin_back_to_panel(lang)
    if callback.message:
        await admin_edit_screen(callback.bot, callback.message.chat.id, callback.message.message_id, text, kb, lang)
    await callback.answer()


@router.message(BroadcastStates.waiting_text, F.text)
async def msg_admin_broadcast_send(message: Message, state: FSMContext) -> None:
    """Send broadcast: text + channel link; 0.05s delay between users."""
    if not message.from_user or message.from_user.id not in get_config().get_admin_ids():
        return
    data = await state.get_data()
    chat_id = data.get("admin_chat_id")
    message_id = data.get("admin_message_id")
    await state.clear()
    config = get_config()
    channel_link = getattr(config, "channel_link", "") or ""
    text = (message.text or "").strip()
    user = await users_queries.get_user(message.from_user.id)
    lang = user.language if user else "ru"
    kb = admin_back_to_panel(lang)
    if not text:
        err = "Пустой текст. Отменено." if lang == "ru" else "Empty text. Canceled."
        if chat_id is not None and message_id is not None:
            await admin_edit_screen(message.bot, int(chat_id), int(message_id), err, kb, lang)
        else:
            await message.answer(err, reply_markup=kb)
        return
    if channel_link:
        body = f"{text}\n\n📱 [News channel]({channel_link})"
    else:
        body = text
    user_ids = await users_queries.get_user_ids_with_notifications()
    bot = message.bot
    sent = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, body)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            log.warning("Broadcast to {} failed: {}", uid, e)
    done_text = get_text("admin_broadcast_done", lang, count=sent)
    if chat_id is not None and message_id is not None:
        await admin_edit_screen(message.bot, int(chat_id), int(message_id), done_text, kb, lang)
    else:
        await message.answer(done_text, reply_markup=kb)

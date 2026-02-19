"""Admin: edit casino settings (min_bet, max_bet, referral_bonus, demo_balance, tech_works_*)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.config import get_config
from bot.database.queries import settings as settings_queries
from bot.database.queries import users as users_queries
from bot.handlers.admin.utils import admin_edit_screen
from bot.keyboards.inline import admin_back_to_panel, admin_settings_keyboard
from bot.templates.texts import get_text
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="admin_settings")


class AdminSetStates(StatesGroup):
    waiting_value = State()


SETTING_KEYS = (
    "min_bet",
    "max_bet",
    "win_coefficient",
    "referral_bonus",
    "demo_balance",
    "deposit_commission",
    "tech_works_global",
    "tech_works_demo",
    "tech_works_real",
)


@router.callback_query(lambda c: c.data == "admin:settings")
async def cb_admin_settings(callback: CallbackQuery, state: FSMContext) -> None:
    """Show settings keyboard."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids():
        await callback.answer()
        return
    await state.clear()
    if not callback.message:
        return
    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "ru"
    settings = await settings_queries.get_settings()
    lines = [
        f"min_bet={settings.min_bet} max_bet={settings.max_bet}",
        f"referral_bonus={settings.referral_bonus} demo_balance={settings.demo_balance}",
        f"win_coefficient={settings.win_coefficient} deposit_commission={settings.deposit_commission}",
        f"tech_global={settings.tech_works_global} tech_demo={settings.tech_works_demo} tech_real={settings.tech_works_real}",
    ]
    text = "Текущие настройки:\n" + "\n".join(lines) if lang == "ru" else "Current settings:\n" + "\n".join(lines)
    kb = admin_settings_keyboard(lang)
    await admin_edit_screen(callback.bot, callback.message.chat.id, callback.message.message_id, text, kb, lang)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("admin:set:"))
async def cb_admin_set_choose(callback: CallbackQuery, state: FSMContext) -> None:
    """Ask for new value for a setting. admin:set:min_bet etc."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids() or not callback.data:
        await callback.answer()
        return
    key = callback.data.replace("admin:set:", "")
    if key not in SETTING_KEYS:
        await callback.answer()
        return
    settings = await settings_queries.get_settings()
    value = getattr(settings, key, None)
    await state.set_state(AdminSetStates.waiting_value)
    await state.update_data(
        admin_set_key=key,
        admin_chat_id=callback.message.chat.id if callback.message else None,
        admin_message_id=callback.message.message_id if callback.message else None,
    )
    user = await users_queries.get_user(callback.from_user.id)
    lang = user.language if user else "ru"
    text = get_text("admin_set_value", lang, key=key, value=value)
    if callback.message:
        await admin_edit_screen(
            callback.bot,
            callback.message.chat.id,
            callback.message.message_id,
            text,
            admin_back_to_panel(lang),
            lang,
        )
    await callback.answer()


@router.message(AdminSetStates.waiting_value, F.text)
async def msg_admin_set_value(message: Message, state: FSMContext) -> None:
    """Apply new setting value."""
    if not message.from_user or message.from_user.id not in get_config().get_admin_ids():
        return
    data = await state.get_data()
    key = data.get("admin_set_key")
    await state.clear()
    if key not in SETTING_KEYS:
        await message.answer("Canceled.")
        return
    raw = (message.text or "").strip()
    if key in ("tech_works_global", "tech_works_demo", "tech_works_real"):
        value = 1 if raw.lower() in ("1", "true", "yes", "on") else 0
    elif key in ("win_coefficient", "deposit_commission"):
        try:
            value = float(raw)
            if value < 0:
                value = 0.0
        except ValueError:
            await message.answer("Invalid number.")
            return
    else:
        try:
            value = int(raw)
            if key in ("min_bet", "max_bet", "referral_bonus", "demo_balance") and value < 0:
                value = 0
        except ValueError:
            await message.answer("Invalid number.")
            return
    await settings_queries.update_settings(**{key: value})
    user = await users_queries.get_user(message.from_user.id)
    lang = user.language if user else "ru"
    text = get_text("admin_set_ok", lang, key=key, value=value)
    kb = admin_back_to_panel(lang)
    chat_id = data.get("admin_chat_id")
    message_id = data.get("admin_message_id")
    if chat_id is not None and message_id is not None:
        await admin_edit_screen(message.bot, int(chat_id), int(message_id), text, kb, lang)
    else:
        await message.answer(text, reply_markup=kb)

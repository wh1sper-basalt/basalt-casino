"""Admin: user search, view profile, block, change balance, user stats."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.config import get_config
from bot.database.queries import users as users_queries
from bot.handlers.admin.utils import admin_edit_screen
from bot.keyboards.inline import admin_back_to_panel, admin_balance_type_choice, admin_block_type_choice, admin_confirm_danger, admin_user_actions
from bot.services.stats import get_user_stats_display  # ← исправлено: правильный импорт
from bot.templates.texts import get_text
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="admin_users")


class AdminUserStates(StatesGroup):
    search = State()
    balance_amount = State()


def _is_admin(user_id: int) -> bool:
    return user_id in get_config().get_admin_ids()


async def _admin_lang(admin_id: int) -> str:
    u = await users_queries.get_user(admin_id)
    return u.language if u else "ru"


@router.callback_query(lambda c: c.data == "admin:users")
async def cb_admin_users(callback: CallbackQuery, state: FSMContext) -> None:
    """Show search prompt: edit same admin message."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids():
        await callback.answer()
        return
    await state.clear()
    if not callback.message:
        return
    await state.set_state(AdminUserStates.search)
    await state.update_data(
        admin_chat_id=callback.message.chat.id,
        admin_message_id=callback.message.message_id,
    )
    lang = await _admin_lang(callback.from_user.id)
    text = get_text("admin_search_prompt", lang)
    kb = admin_back_to_panel(lang)
    await admin_edit_screen(callback.bot, callback.message.chat.id, callback.message.message_id, text, kb, lang)
    await callback.answer()


@router.message(AdminUserStates.search, F.text)
async def msg_admin_search(message: Message, state: FSMContext) -> None:
    """Process search: edit admin message with result (user list or not found)."""
    if not message.from_user or message.from_user.id not in get_config().get_admin_ids():
        return
    data = await state.get_data()
    chat_id = data.get("admin_chat_id")
    message_id = data.get("admin_message_id")
    await state.clear()
    query = (message.text or "").strip()
    if not query:
        return
    users = await users_queries.find_users_by_query(query, limit=15)
    lang = await _admin_lang(message.from_user.id)
    kb = admin_back_to_panel(lang)
    if not users:
        text = get_text("admin_user_not_found", lang)
        if chat_id is not None and message_id is not None:
            await admin_edit_screen(message.bot, int(chat_id), int(message_id), text, kb, lang)
        else:
            await message.answer(text, reply_markup=kb)
        return
    if len(users) == 1 and chat_id is not None and message_id is not None:
        await _edit_admin_message_user_profile(message.bot, int(chat_id), int(message_id), users[0], lang)
        return
    if len(users) == 1:
        await _send_user_profile(message, users[0])
        return
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    buttons = []
    for u in users[:10]:
        label = f"{u.user_id} @{u.username or 'n/a'}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"admin:user:{u.user_id}")])
    buttons.append([InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin:users")])
    text = "Выберите пользователя:" if lang == "ru" else "Select user:"
    if chat_id is not None and message_id is not None:
        await admin_edit_screen(
            message.bot,
            int(chat_id),
            int(message_id),
            text,
            InlineKeyboardMarkup(inline_keyboard=buttons),
            lang,
        )
    else:
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


async def _user_profile_caption_and_kb(user: object, lang: str):
    """Build (caption, kb) for user profile view."""
    balance = await users_queries.get_user_balance(user.user_id)
    real = balance.real_balance if balance else 0
    demo = balance.demo_balance if balance else 0
    blocked = "Да" if (user.is_blocked and lang == "ru") else "Нет" if (not user.is_blocked and lang == "ru") else "Yes" if user.is_blocked else "No"
    if user.is_blocked and user.block_type:
        blocked = f"{blocked} ({user.block_type})"
    caption = get_text(
        "admin_user_caption",
        lang,
        user_id=user.user_id,
        username=user.username or "n/a",
        full_name=user.full_name or "—",
        blocked=blocked,
        real=real,
        demo=demo,
    )
    return caption, admin_user_actions(user.user_id, lang)


async def _edit_admin_message_user_profile(bot, chat_id: int, message_id: int, user: object, lang: str) -> None:
    """Edit admin message to show user profile (same image + caption + kb)."""
    caption, kb = await _user_profile_caption_and_kb(user, lang)
    await admin_edit_screen(bot, chat_id, message_id, caption, kb, lang)


async def _send_user_profile(message: Message, user: object) -> None:
    """Send user profile (fallback when no admin message id)."""
    lang = await _admin_lang(message.from_user.id) if message.from_user else "ru"
    caption, kb = await _user_profile_caption_and_kb(user, lang)
    await message.answer(caption, reply_markup=kb)


@router.callback_query(lambda c: c.data and c.data.startswith("admin:user:") and c.data.count(":") == 2)
async def cb_admin_user_view(callback: CallbackQuery) -> None:
    """Show one user profile by id (admin:user:123)."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids() or not callback.data:
        await callback.answer()
        return
    try:
        user_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer()
        return
    user = await users_queries.get_user(user_id)
    if not user:
        lang = await _admin_lang(callback.from_user.id)
        await callback.answer(get_text("admin_user_not_found", lang), show_alert=True)
        return
    lang = await _admin_lang(callback.from_user.id)
    balance = await users_queries.get_user_balance(user_id)
    real = balance.real_balance if balance else 0
    demo = balance.demo_balance if balance else 0
    blocked = "Да" if (user.is_blocked and lang == "ru") else "Нет" if (not user.is_blocked and lang == "ru") else "Yes" if user.is_blocked else "No"
    if user.is_blocked and user.block_type:
        blocked = f"{blocked} ({user.block_type})"
    caption = get_text(
        "admin_user_caption",
        lang,
        user_id=user.user_id,
        username=user.username or "n/a",
        full_name=user.full_name or "—",
        blocked=blocked,
        real=real,
        demo=demo,
    )
    kb = admin_user_actions(user_id, lang)
    if callback.message:
        await admin_edit_screen(callback.bot, callback.message.chat.id, callback.message.message_id, caption, kb, lang)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("admin:user:") and "block" in c.data)
async def cb_admin_user_block(callback: CallbackQuery) -> None:
    """Show block type choice (full/partial/none)."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids() or not callback.data:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer()
        return
    try:
        user_id = int(parts[2])
    except ValueError:
        await callback.answer()
        return
    lang = await _admin_lang(callback.from_user.id)
    kb = admin_block_type_choice(user_id, lang)
    text = "Выберите тип блокировки:" if lang == "ru" else "Choose block type:"
    if callback.message:
        await admin_edit_screen(callback.bot, callback.message.chat.id, callback.message.message_id, text, kb, lang)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("admin:block:"))
async def cb_admin_block_confirm(callback: CallbackQuery) -> None:
    """Show confirm for block (full/partial) or apply unblock. admin:block:user_id:full|partial|none."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids() or not callback.data:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return
    try:
        user_id = int(parts[2])
    except ValueError:
        await callback.answer()
        return
    block_type = parts[3]
    lang = await _admin_lang(callback.from_user.id)
    if block_type == "none":
        await users_queries.set_block(user_id, is_blocked=False, block_type=None)
        user = await users_queries.get_user(user_id)
        if callback.message and user:
            balance = await users_queries.get_user_balance(user_id)
            real = balance.real_balance if balance else 0
            demo = balance.demo_balance if balance else 0
            no_label = "Нет" if lang == "ru" else "No"
            caption = get_text(
                "admin_user_caption",
                lang,
                user_id=user.user_id,
                username=user.username or "n/a",
                full_name=user.full_name or "—",
                blocked=no_label,
                real=real,
                demo=demo,
            )
            await admin_edit_screen(
                callback.bot,
                callback.message.chat.id,
                callback.message.message_id,
                caption,
                admin_user_actions(user_id, lang),
                lang,
            )
        await callback.answer("Разблокировано." if lang == "ru" else "Unblocked.")
        return
    kb = admin_confirm_danger(f"block_{block_type}", user_id, lang)
    confirm_text = f"Подтвердить блокировку ({block_type}) для user {user_id}?" if lang == "ru" else f"Confirm block ({block_type}) for user {user_id}?"
    if callback.message:
        await admin_edit_screen(
            callback.bot,
            callback.message.chat.id,
            callback.message.message_id,
            confirm_text,
            kb,
            lang,
        )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("admin:confirm:block_"))
async def cb_admin_block_apply(callback: CallbackQuery) -> None:
    """Apply block after confirm. admin:confirm:block_full:user_id | block_partial:user_id."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids() or not callback.data:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return
    try:
        user_id = int(parts[3])
    except ValueError:
        await callback.answer()
        return
    action = parts[2]
    block_type = "full" if "full" in action else "partial"
    lang = await _admin_lang(callback.from_user.id)
    await users_queries.set_block(user_id, is_blocked=True, block_type=block_type)
    user = await users_queries.get_user(user_id)
    if callback.message and user:
        balance = await users_queries.get_user_balance(user_id)
        real = balance.real_balance if balance else 0
        demo = balance.demo_balance if balance else 0
        blocked = f"Да ({block_type})" if lang == "ru" else f"Yes ({block_type})"
        caption = get_text(
            "admin_user_caption",
            lang,
            user_id=user.user_id,
            username=user.username or "n/a",
            full_name=user.full_name or "—",
            blocked=blocked,
            real=real,
            demo=demo,
        )
        await admin_edit_screen(
            callback.bot,
            callback.message.chat.id,
            callback.message.message_id,
            caption,
            admin_user_actions(user_id, lang),
            lang,
        )
    await callback.answer("Заблокировано." if lang == "ru" else "Blocked.")


@router.callback_query(lambda c: c.data and c.data.startswith("admin:user:") and "balance" in c.data)
async def cb_admin_user_balance_choice(callback: CallbackQuery) -> None:
    """Show balance type: real or demo."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids() or not callback.data:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer()
        return
    try:
        user_id = int(parts[2])
    except ValueError:
        await callback.answer()
        return
    lang = await _admin_lang(callback.from_user.id)
    kb = admin_balance_type_choice(user_id, lang)
    text = "Выберите баланс для изменения:" if lang == "ru" else "Choose balance to edit:"
    if callback.message:
        await admin_edit_screen(callback.bot, callback.message.chat.id, callback.message.message_id, text, kb, lang)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("admin:balance:"))
async def cb_admin_balance_enter(callback: CallbackQuery, state: FSMContext) -> None:
    """Ask for new balance amount (FSM). admin:balance:user_id:real|demo."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids() or not callback.data:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return
    try:
        user_id = int(parts[2])
    except ValueError:
        await callback.answer()
        return
    balance_type = parts[3]
    await state.set_state(AdminUserStates.balance_amount)
    await state.update_data(
        admin_balance_user_id=user_id,
        admin_balance_type=balance_type,
        admin_chat_id=callback.message.chat.id if callback.message else None,
        admin_message_id=callback.message.message_id if callback.message else None,
    )
    lang = await _admin_lang(callback.from_user.id)
    text = "Введите новую сумму баланса (целое число):" if lang == "ru" else "Send new balance amount (integer):"
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


@router.message(AdminUserStates.balance_amount, F.text)
async def msg_admin_balance_amount(message: Message, state: FSMContext) -> None:
    """Apply new balance and edit admin message to show user profile."""
    if not message.from_user or message.from_user.id not in get_config().get_admin_ids():
        return
    data = await state.get_data()
    user_id = data.get("admin_balance_user_id")
    balance_type = data.get("admin_balance_type")
    admin_chat_id = data.get("admin_chat_id")
    admin_message_id = data.get("admin_message_id")
    await state.clear()
    if user_id is None or balance_type not in ("real", "demo"):
        await message.answer("Error. Start from admin panel.")
        return
    try:
        amount = int((message.text or "").strip())
        if amount < 0:
            amount = 0
    except ValueError:
        await message.answer("Invalid number. Send an integer.")
        return
    if balance_type == "real":
        await users_queries.update_balance(user_id, real_balance=amount)
    else:
        await users_queries.update_balance(user_id, demo_balance=amount)
    user = await users_queries.get_user(user_id)
    if not user:
        await message.answer("Done.")
        return
    lang = await _admin_lang(message.from_user.id)
    balance = await users_queries.get_user_balance(user_id)
    real = balance.real_balance if balance else 0
    demo = balance.demo_balance if balance else 0
    blocked = "Да" if (user.is_blocked and lang == "ru") else "Нет" if (not user.is_blocked and lang == "ru") else "Yes" if user.is_blocked else "No"
    if user.block_type:
        blocked = f"{blocked} ({user.block_type})"
    caption = get_text(
        "admin_user_caption",
        lang,
        user_id=user.user_id,
        username=user.username or "n/a",
        full_name=user.full_name or "—",
        blocked=blocked,
        real=real,
        demo=demo,
    )
    kb = admin_user_actions(user_id, lang)
    if admin_chat_id is not None and admin_message_id is not None:
        await admin_edit_screen(message.bot, int(admin_chat_id), int(admin_message_id), caption, kb, lang)
    else:
        await message.answer(caption, reply_markup=kb)


@router.callback_query(lambda c: c.data and c.data.startswith("admin:cancel:"))
async def cb_admin_cancel(callback: CallbackQuery) -> None:
    """Cancel dangerous action: return to user view. admin:cancel:action_key:user_id."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids() or not callback.data:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return
    try:
        user_id = int(parts[3])
    except ValueError:
        await callback.answer()
        return
    lang = await _admin_lang(callback.from_user.id)
    user = await users_queries.get_user(user_id)
    if not user:
        await callback.answer(get_text("admin_user_not_found", lang), show_alert=True)
        return
    balance = await users_queries.get_user_balance(user_id)
    real = balance.real_balance if balance else 0
    demo = balance.demo_balance if balance else 0
    blocked = "Да" if (user.is_blocked and lang == "ru") else "Нет" if (not user.is_blocked and lang == "ru") else "Yes" if user.is_blocked else "No"
    if user.block_type:
        blocked = f"{blocked} ({user.block_type})"
    caption = get_text(
        "admin_user_caption",
        lang,
        user_id=user.user_id,
        username=user.username or "n/a",
        full_name=user.full_name or "—",
        blocked=blocked,
        real=real,
        demo=demo,
    )
    if callback.message:
        await admin_edit_screen(
            callback.bot,
            callback.message.chat.id,
            callback.message.message_id,
            caption,
            admin_user_actions(user_id, lang),
            lang,
        )
    await callback.answer("Отменено." if lang == "ru" else "Canceled.")


@router.callback_query(lambda c: c.data and c.data.startswith("admin:user:") and "stats" in c.data)
async def cb_admin_user_stats(callback: CallbackQuery) -> None:
    """Show user stats (total_games, wins, etc.)."""
    if not callback.from_user or callback.from_user.id not in get_config().get_admin_ids() or not callback.data:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer()
        return
    try:
        user_id = int(parts[2])
    except ValueError:
        await callback.answer()
        return
    lang = await _admin_lang(callback.from_user.id)
    stats = await get_user_stats_display(user_id)  # ← теперь работает
    lines = [
        f"Games: {stats['total_games']}",
        f"Wins: {stats['total_wins']} Losses: {stats['total_losses']}",
        f"Win rate: {stats['win_rate']}%",
        f"Deposited: {stats['total_deposited']}₽ Withdrawn: {stats['total_withdrawn']}₽",
        f"Won: {stats['total_won']}₽ Lost: {stats['total_lost']}₽",
    ]
    caption = "Статистика пользователя:\n" + "\n".join(lines) if lang == "ru" else "User stats:\n" + "\n".join(lines)
    kb = admin_user_actions(user_id, lang)
    if callback.message:
        await admin_edit_screen(callback.bot, callback.message.chat.id, callback.message.message_id, caption, kb, lang)
    await callback.answer()

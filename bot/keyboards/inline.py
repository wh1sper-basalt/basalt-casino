"""Inline keyboards (pure functions returning InlineKeyboardMarkup)."""

from __future__ import annotations

from typing import Dict, List
from urllib.parse import quote

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.templates.texts import get_text


def main_menu(lang: str) -> InlineKeyboardMarkup:
    """Main menu: Play first, then Account. row_width=1."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text("btn_play", lang),
                    callback_data="menu:play",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=get_text("btn_account", lang),
                    callback_data="menu:account",
                ),
            ],
        ]
    )


def account_menu(
    lang: str,
    *,
    need_demo_restore: bool = False,
    demo_mode: bool = True,
) -> InlineKeyboardMarkup:
    """Account: Statistics, Settings; Mode, Deposit; Become a referral; [Restore demo]; Back. (Withdraw is in Deposit screen.)"""
    rows = [
        [
            InlineKeyboardButton(text=get_text("btn_stats", lang), callback_data="menu:stats"),
            InlineKeyboardButton(text=get_text("btn_settings", lang), callback_data="menu:settings"),
        ],
        [
            InlineKeyboardButton(text=get_text("btn_mode", lang), callback_data="menu:mode"),
            InlineKeyboardButton(text=get_text("btn_deposit", lang), callback_data="menu:deposit"),
        ],
        [
            InlineKeyboardButton(text=get_text("btn_referral", lang), callback_data="menu:referral"),
        ],
    ]
    if need_demo_restore:
        rows.append([InlineKeyboardButton(text=get_text("btn_restore_demo", lang), callback_data="demo:restore")])
    rows.append([InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="menu:back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def referral_menu(lang: str, link: str, share_text: str) -> InlineKeyboardMarkup:
    """Referral screen: Share (tg://msg) and Back."""
    from urllib.parse import quote

    share_url = f"https://t.me/share/url?url={quote(link)}&text={quote(share_text)}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("btn_share", lang), url=share_url)],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="account:back")],
        ]
    )


def settings_menu(lang: str, notifications: bool, fast_mode: bool) -> InlineKeyboardMarkup:
    """Settings: Notifications (✅/❌), FAST MODE (✅/❌), Language, Back."""
    notif_text = get_text("notifications_on", lang) if notifications else get_text("notifications_off", lang)
    fast_text = get_text("fast_mode_on", lang) if fast_mode else get_text("fast_mode_off", lang)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=notif_text, callback_data="settings:notif"),
                InlineKeyboardButton(text=fast_text, callback_data="settings:fast"),
            ],
            [InlineKeyboardButton(text=get_text("btn_language", lang), callback_data="menu:language")],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="account:back")],
        ]
    )


def mode_switch(lang: str, current_demo: bool) -> InlineKeyboardMarkup:
    """Mode: one button to switch (to Real or to DEMO), Back."""
    if current_demo:
        btn_text = get_text("btn_switch_to_real", lang)
        callback_data = "mode:switch_real"
    else:
        btn_text = get_text("btn_switch_to_demo", lang)
        callback_data = "mode:switch_demo"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=btn_text, callback_data=callback_data)],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="account:back")],
        ]
    )


def language_switch(lang: str) -> InlineKeyboardMarkup:
    """Language: RU, EN; Back."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("btn_lang_ru", lang), callback_data="lang:ru"),
                InlineKeyboardButton(text=get_text("btn_lang_en", lang), callback_data="lang:en"),
            ],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="account:back")],
        ]
    )


def deposit_menu(lang: str, *, has_contact_sent: bool = False) -> InlineKeyboardMarkup:
    """Deposit: row1 Пополнить, Вывод; row2 Мои заявки; row3 Отправить контакт (if not sent); last Назад."""
    rows = [
        [
            InlineKeyboardButton(text=get_text("btn_topup", lang), callback_data="deposit:topup"),
            InlineKeyboardButton(text=get_text("btn_withdraw", lang), callback_data="menu:withdraw"),
        ],
        [InlineKeyboardButton(text=get_text("btn_my_requests", lang), callback_data="menu:payment_status")],
    ]
    if not has_contact_sent:
        rows.append([InlineKeyboardButton(text=get_text("btn_send_contact", lang), callback_data="deposit:contact")])
    rows.append([InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="account:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_status_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Ваши заявки: одна кнопка Назад — возврат в меню Депозита."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="menu:deposit")],
        ]
    )


def deposit_contact_screen_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Contact screen: Подтвердить (share contact), Назад to deposit."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text("contact_btn_confirm", lang),
                    callback_data="deposit:contact_confirm",
                )
            ],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="deposit:cancel")],
        ]
    )


def deposit_amounts(lang: str, min_bet: int, max_bet: int, presets: List[int]) -> InlineKeyboardMarkup:
    """Deposit amount: min_bet, presets (up to 4), Custom amount, Cancel."""
    buttons = []
    row = [InlineKeyboardButton(text=f"{min_bet} ₽", callback_data=f"deposit:amount:{min_bet}")]
    for p in presets:
        if p != min_bet:
            row.append(InlineKeyboardButton(text=f"{p} ₽", callback_data=f"deposit:amount:{p}"))
        if len(row) >= 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=get_text("btn_custom_amount", lang), callback_data="deposit:custom")])
    buttons.append([InlineKeyboardButton(text=get_text("btn_cancel", lang), callback_data="deposit:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def deposit_confirm_amount(lang: str, amount: int) -> InlineKeyboardMarkup:
    """After amount chosen: Create request, Back."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text("btn_create_request", lang),
                    callback_data=f"deposit:create:{amount}",
                )
            ],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="deposit:cancel")],
        ]
    )


def withdraw_amounts(lang: str, min_bet: int, max_bet: int, presets: List[int]) -> InlineKeyboardMarkup:
    """Withdraw amount: min_bet, presets, Custom amount, Cancel (back to account)."""
    buttons = []
    row = [InlineKeyboardButton(text=f"{min_bet} ₽", callback_data=f"withdraw:amount:{min_bet}")]
    for p in presets:
        if p != min_bet:
            row.append(InlineKeyboardButton(text=f"{p} ₽", callback_data=f"withdraw:amount:{p}"))
        if len(row) >= 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=get_text("btn_custom_amount", lang), callback_data="withdraw:custom")])
    buttons.append([InlineKeyboardButton(text=get_text("btn_cancel", lang), callback_data="withdraw:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def withdraw_confirm_amount(lang: str, amount: int) -> InlineKeyboardMarkup:
    """After withdraw amount chosen: Create request, Back."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text("btn_create_request", lang),
                    callback_data=f"withdraw:create:{amount}",
                )
            ],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="account:back")],
        ]
    )


def deposit_change_amount(lang: str) -> InlineKeyboardMarkup:
    """Change amount button for deposit confirmation screen."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("btn_change_amount", lang), callback_data="deposit:change")],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="deposit:cancel")],
        ]
    )


def withdraw_change_amount(lang: str) -> InlineKeyboardMarkup:
    """Change amount button for withdraw confirmation screen."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("btn_change_amount", lang), callback_data="withdraw:change")],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="withdraw:cancel")],
        ]
    )


def stats_menu(lang: str, webapp_url: str | None = None) -> InlineKeyboardMarkup:
    """Stats menu: Reset (UI only) and Back to account."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("btn_stats_reset", lang), callback_data="stats:reset")],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="account:back")],
        ]
    )


# ----- Games -----
def games_list(lang: str) -> InlineKeyboardMarkup:
    """Eight game buttons from GAME_LIST + Back (to main). row_width=2."""
    from bot.core.games import GAME_LIST
    from bot.templates.texts import get_text

    buttons = []
    row = []
    for gid in sorted(GAME_LIST.keys()):
        game = GAME_LIST[gid]
        name_key = game.get("name_key", f"game_name_{gid}")
        name = get_text(name_key, lang)

        row.append(InlineKeyboardButton(text=name, callback_data=f"game:{gid}:bet"))
        if len(row) >= 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="menu:back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def game_description_keyboard(lang: str, game_id: int) -> InlineKeyboardMarkup:
    """Game description screen: Make bet (-> outcome selection), Cancel (-> list)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("game_make_bet", lang), callback_data=f"game:{game_id}:outcomes")],
            [InlineKeyboardButton(text=get_text("btn_cancel", lang), callback_data="game:list")],
        ]
    )


def game_outcomes(lang: str, game_id: int, outcomes: List[str]) -> InlineKeyboardMarkup:
    """Outcome buttons: callback_data game:GID:o:OID, row_width=2, then Cancel (back to description)."""
    buttons = []
    row = []
    for i, out in enumerate(outcomes):
        row.append(InlineKeyboardButton(text=out, callback_data=f"game:{game_id}:o:{i}"))
        if len(row) >= 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=get_text("btn_cancel", lang), callback_data=f"game:{game_id}:bet")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def game_bet_amounts(
    lang: str,
    game_id: int,
    outcome_index: int,
    min_bet: int,
    presets: List[int],
    preset_buttons: List[str] = None,
) -> InlineKeyboardMarkup:
    """Bet amount buttons for game: game:GID:o:OID:a:AMT, Custom, Back."""
    buttons = []
    row = []

    # Use provided button texts or fallback to numbers
    if preset_buttons and len(preset_buttons) == len(presets):
        button_texts = preset_buttons
    else:
        button_texts = [f"{p} ₽" for p in presets]

    for i, p in enumerate(presets):
        row.append(InlineKeyboardButton(text=button_texts[i], callback_data=f"game:{game_id}:o:{outcome_index}:a:{p}"))
        if len(row) >= 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append(
        [
            InlineKeyboardButton(
                text=get_text("btn_custom_amount", lang),
                callback_data=f"game:{game_id}:o:{outcome_index}:custom",
            )
        ]
    )
    buttons.append([InlineKeyboardButton(text=get_text("btn_back", lang), callback_data=f"game:{game_id}:bet")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_bet(
    lang: str,
    game_id: int,
    outcome_index: int,
    amount: int,
) -> InlineKeyboardMarkup:
    """Place bet, Change amount, Change outcome, Cancel."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text("btn_place_bet", lang),
                    callback_data=f"game:{game_id}:o:{outcome_index}:place:{amount}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=get_text("btn_change_amount", lang),
                    callback_data=f"game:{game_id}:o:{outcome_index}",
                ),
                InlineKeyboardButton(
                    text=get_text("btn_change_outcome", lang),
                    callback_data=f"game:{game_id}:outcomes",
                ),
            ],
            [InlineKeyboardButton(text=get_text("btn_cancel", lang), callback_data="game:list")],
        ]
    )


def game_result_actions(
    lang: str,
    game_id: int | None = None,
    outcome_index: int | None = None,
    amount: int | None = None,
    confirm_msg_id: int | None = None,
    dice_msg_ids: list[int] | None = None,
) -> InlineKeyboardMarkup:
    """Result screen: Repeat (same params) and Exit only."""
    if game_id is not None and outcome_index is not None and amount is not None:
        repeat_data = f"game:repeat:{game_id}:{outcome_index}:{amount}"
    else:
        repeat_data = "game:list"
    if confirm_msg_id is not None and dice_msg_ids is not None and len(dice_msg_ids) > 0:
        exit_data = f"game:exit_cleanup:{confirm_msg_id}:{':'.join(map(str, dice_msg_ids))}"
    else:
        exit_data = "game:exit_cleanup"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("btn_repeat", lang), callback_data=repeat_data)],
            [InlineKeyboardButton(text=get_text("btn_exit", lang), callback_data=exit_data)],
        ]
    )


# ----- Info / Help -----
def info_buttons(telegraph_urls: Dict[str, str], lang: str = "en") -> InlineKeyboardMarkup:
    """Info: Rules, Game rules, Deposit, Support, FAQ (Telegraph URLs), Close. Layout 1-2-2-1."""

    def url(key: str) -> str:
        return telegraph_urls.get(key) or "#"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("info_btn_rules", lang), url=url("rules"))],
            [
                InlineKeyboardButton(text=get_text("info_btn_rules_games", lang), url=url("rules_games")),
                InlineKeyboardButton(text=get_text("info_btn_deposit", lang), url=url("deposit")),
            ],
            [
                InlineKeyboardButton(text=get_text("info_btn_support", lang), url=url("support")),
                InlineKeyboardButton(text=get_text("info_btn_faq", lang), url=url("faq")),
            ],
            [InlineKeyboardButton(text=get_text("btn_close", lang), callback_data="info:close")],
        ]
    )


def help_buttons(admin_username: str, start_text: str, lang: str = "en") -> InlineKeyboardMarkup:
    """Help: Write (t.me/username?text=...), Close."""
    write_url = f"https://t.me/{admin_username.lstrip('@')}?text={quote(start_text)}" if admin_username else "#"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("help_btn_write", lang), url=write_url)],
            [InlineKeyboardButton(text=get_text("btn_close", lang), callback_data="help:close")],
        ]
    )


# ----- Admin -----
def admin_main_menu(lang: str = "ru") -> InlineKeyboardMarkup:
    """Admin panel: 2 columns [Users, Settings] [Payments, Stats], then [Broadcast], then [Exit] (deletes message)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("admin_btn_users", lang), callback_data="admin:users"),
                InlineKeyboardButton(text=get_text("admin_btn_settings", lang), callback_data="admin:settings"),
            ],
            [
                InlineKeyboardButton(text=get_text("admin_btn_payments", lang), callback_data="admin:payments"),
                InlineKeyboardButton(text=get_text("admin_btn_stats", lang), callback_data="admin:stats"),
            ],
            [InlineKeyboardButton(text=get_text("admin_btn_broadcast", lang), callback_data="admin:broadcast")],
            [InlineKeyboardButton(text=get_text("admin_btn_exit", lang), callback_data="admin:exit")],
        ]
    )


def admin_back_to_panel(lang: str = "ru") -> InlineKeyboardMarkup:
    """Single button: Back to admin panel."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin:panel")],
        ]
    )


def admin_user_actions(user_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """User actions: Block, Change balance, Stats, Back."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text("admin_btn_block", lang),
                    callback_data=f"admin:user:{user_id}:block",
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text("admin_btn_balance", lang),
                    callback_data=f"admin:user:{user_id}:balance",
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text("admin_btn_user_stats", lang),
                    callback_data=f"admin:user:{user_id}:stats",
                )
            ],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin:users")],
        ]
    )


def admin_confirm_danger(action_key: str, target_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Confirm dangerous action: action_key e.g. block_full, balance_real; target_id = user_id or request_id."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text("admin_btn_confirm", lang),
                    callback_data=f"admin:confirm:{action_key}:{target_id}",
                ),
                InlineKeyboardButton(
                    text=get_text("btn_cancel", lang),
                    callback_data=f"admin:cancel:{action_key}:{target_id}",
                ),
            ],
        ]
    )


def admin_block_type_choice(user_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Choose block type: full, partial, unblock."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text("admin_block_full", lang),
                    callback_data=f"admin:block:{user_id}:full",
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text("admin_block_partial", lang),
                    callback_data=f"admin:block:{user_id}:partial",
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text("admin_block_unblock", lang),
                    callback_data=f"admin:block:{user_id}:none",
                )
            ],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data=f"admin:user:{user_id}")],
        ]
    )


def admin_balance_type_choice(user_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Choose balance to edit: real, demo."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text("admin_balance_real", lang),
                    callback_data=f"admin:balance:{user_id}:real",
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text("admin_balance_demo", lang),
                    callback_data=f"admin:balance:{user_id}:demo",
                )
            ],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data=f"admin:user:{user_id}")],
        ]
    )


def admin_payments_list_keyboard(pending: list, lang: str = "ru") -> InlineKeyboardMarkup:
    """List of pending requests: each row = request id (view opens approve/reject)."""
    buttons = []
    for req in pending[:15]:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"#{req.id} {req.request_type} {req.amount}₽",
                    callback_data=f"admin:pay:view:{req.id}",
                ),
            ]
        )
    buttons.append([InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin:panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_payment_actions(request_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    """Approve / Reject / Back for one payment request (in admin panel list view)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text("admin_btn_approve", lang),
                    callback_data=f"admin:pay:approve:{request_id}",
                ),
                InlineKeyboardButton(
                    text=get_text("admin_btn_reject", lang),
                    callback_data=f"admin:pay:reject:{request_id}",
                ),
            ],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin:payments")],
        ]
    )


def admin_new_request_notification_keyboard(request_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Inline for notification sent to admin in PM: Подтвердить, Отклонить, Прочитано (delete message)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text("admin_btn_approve", lang),
                    callback_data=f"admin:pay:approve:{request_id}",
                ),
                InlineKeyboardButton(
                    text=get_text("admin_btn_reject", lang),
                    callback_data=f"admin:pay:reject:{request_id}",
                ),
            ],
            [InlineKeyboardButton(text=get_text("admin_btn_read", lang), callback_data="admin:pay:dismiss")],
        ]
    )


def admin_settings_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Settings list: min_bet, max_bet, win_coefficient, referral_bonus, demo_balance, deposit_commission, tech_works_*."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="min_bet", callback_data="admin:set:min_bet"),
                InlineKeyboardButton(text="max_bet", callback_data="admin:set:max_bet"),
            ],
            [
                InlineKeyboardButton(text="referral_bonus", callback_data="admin:set:referral_bonus"),
                InlineKeyboardButton(text="demo_balance", callback_data="admin:set:demo_balance"),
            ],
            [
                InlineKeyboardButton(text="win_coef", callback_data="admin:set:win_coefficient"),
                InlineKeyboardButton(text="dep_commission", callback_data="admin:set:deposit_commission"),
            ],
            [
                InlineKeyboardButton(text="tech_global", callback_data="admin:set:tech_works_global"),
                InlineKeyboardButton(text="tech_demo", callback_data="admin:set:tech_works_demo"),
                InlineKeyboardButton(text="tech_real", callback_data="admin:set:tech_works_real"),
            ],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin:panel")],
        ]
    )

"""Business logic: game, balance, referral, stats, demo, notify."""

from bot.services.balance import check_sufficient, credit_deposit, credit_referral_bonus, credit_win, deduct_bet, deduct_withdraw
from bot.services.demo import can_restore_demo, perform_demo_restore
from bot.services.game import calculate_win_amount, get_game_info, get_probability, resolve_outcome
from bot.services.notify_admin import notify_admins_new_payment_request
from bot.services.notify_referrer import notify_referrer_new_referral
from bot.services.referral import generate_referral_link, process_referral_bonuses, validate_referral_link
from bot.services.stats import get_user_stats_display

__all__ = [
    # balance
    "check_sufficient",
    "deduct_bet",
    "credit_win",
    "credit_referral_bonus",
    "credit_deposit",
    "deduct_withdraw",
    # referral
    "generate_referral_link",
    "process_referral_bonuses",
    "validate_referral_link",
    # notify
    "notify_referrer_new_referral",
    "notify_admins_new_payment_request",
    # game
    "get_game_info",
    "get_probability",
    "resolve_outcome",
    "calculate_win_amount",
    # stats
    "get_user_stats_display",
    # demo
    "can_restore_demo",
    "perform_demo_restore",
]

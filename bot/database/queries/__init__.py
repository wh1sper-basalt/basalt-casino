"""Database queries by entity."""

from bot.database.queries.demo_accounts import get_demo_account, upsert_demo_reset
from bot.database.queries.games import get_games_count, get_last_games_by_user, save_game
from bot.database.queries.payments import create_payment_request, get_payment_request, get_pending_requests, get_requests_by_user, set_payment_status
from bot.database.queries.referrals import add_referral, count_referrals_by_referrer, get_referrer_by_user, referral_exists, set_bonus_credited
from bot.database.queries.settings import get_settings, update_settings
from bot.database.queries.user_stats import get_or_create_stats, update_stats_after_game, update_stats_after_payment
from bot.database.queries.users import create_user, get_language, get_user, set_block, set_fast_mode, set_notifications, update_balance, update_user

__all__ = [
    "get_user",
    "create_user",
    "update_user",
    "update_balance",
    "set_block",
    "get_language",
    "set_fast_mode",
    "set_notifications",
    "get_settings",
    "update_settings",
    "save_game",
    "get_last_games_by_user",
    "get_games_count",
    "create_payment_request",
    "get_pending_requests",
    "get_requests_by_user",
    "get_payment_request",
    "set_payment_status",
    "add_referral",
    "get_referrer_by_user",
    "count_referrals_by_referrer",
    "set_bonus_credited",
    "referral_exists",
    "get_demo_account",
    "upsert_demo_reset",
    "get_or_create_stats",
    "update_stats_after_game",
    "update_stats_after_payment",
]

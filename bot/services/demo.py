"""Demo balance restore: can_restore_demo (24h cooldown), perform_demo_restore."""

from __future__ import annotations

from datetime import datetime, timezone

from bot.core.constants import DEMO_RESTORE_INTERVAL_SECONDS
from bot.database.queries import demo_accounts as demo_queries
from bot.database.queries import settings as settings_queries
from bot.database.queries import users as users_queries


async def can_restore_demo(user_id: int) -> tuple[bool, int]:
    """
    Check if user can restore demo balance (balance < min_bet and 24h passed since last reset).

    Returns:
        (allowed, seconds_remaining): (True, 0) if restore allowed;
            (False, 0) if balance >= min_bet; (False, seconds) if cooldown not passed.
    """
    settings = await settings_queries.get_settings()
    balance_row = await users_queries.get_user_balance(user_id)
    if balance_row is None:
        return (False, 0)
    if balance_row.demo_balance >= settings.min_bet:
        return (False, 0)
    demo_acc = await demo_queries.get_demo_account(user_id)
    now = datetime.now(timezone.utc)
    if demo_acc is None or demo_acc.last_reset is None:
        return (True, 0)
    try:
        last = datetime.fromisoformat(demo_acc.last_reset.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return (True, 0)
    elapsed = (now - last).total_seconds()
    if elapsed >= DEMO_RESTORE_INTERVAL_SECONDS:
        return (True, 0)
    return (False, int(DEMO_RESTORE_INTERVAL_SECONDS - elapsed))


async def perform_demo_restore(user_id: int) -> None:
    """
    Set demo_balance to settings.demo_balance and update demo_accounts (last_reset, reset_count).
    """
    settings = await settings_queries.get_settings()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    await users_queries.update_balance(user_id, demo_balance=settings.demo_balance)
    await demo_queries.upsert_demo_reset(user_id, now)

"""Tests for demo restore: can_restore_demo (24h, balance < min_bet), perform_demo_restore."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from bot.services.demo import can_restore_demo, perform_demo_restore


@pytest.mark.asyncio
async def test_can_restore_demo_first_time_allowed(db, test_user: int) -> None:
    """When balance < min_bet and no last_reset (new user), can_restore_demo returns (True, 0)."""
    allowed, secs = await can_restore_demo(test_user)
    assert allowed is True
    assert secs == 0


@pytest.mark.asyncio
async def test_can_restore_demo_balance_sufficient_not_allowed(db, test_user: int) -> None:
    """When demo_balance >= min_bet, can_restore_demo returns (False, 0)."""
    from bot.database.queries import users as users_queries

    await users_queries.update_balance(test_user, demo_balance=50000)
    allowed, secs = await can_restore_demo(test_user)
    assert allowed is False
    assert secs == 0


@pytest.mark.asyncio
async def test_perform_demo_restore_sets_balance_and_reset(db, test_user: int) -> None:
    """perform_demo_restore sets demo_balance to settings.demo_balance and updates last_reset."""
    from bot.database.queries import demo_accounts as demo_queries
    from bot.database.queries import users as users_queries

    await perform_demo_restore(test_user)
    row = await users_queries.get_user_balance(test_user)
    assert row is not None
    assert row.demo_balance == 50000  # from settings in conftest
    acc = await demo_queries.get_demo_account(test_user)
    assert acc is not None
    assert acc.last_reset is not None
    assert acc.reset_count >= 1


@pytest.mark.asyncio
async def test_can_restore_demo_cooldown(db, test_user: int) -> None:
    """When balance < min_bet but last_reset was just set, can_restore_demo returns (False, seconds_remaining)."""
    from bot.database.queries import demo_accounts as demo_queries
    from bot.database.queries import users as users_queries

    await users_queries.update_balance(test_user, demo_balance=50)  # below min_bet
    now = datetime.now(timezone.utc)
    await demo_queries.upsert_demo_reset(test_user, now.strftime("%Y-%m-%dT%H:%M:%SZ"))
    allowed, secs = await can_restore_demo(test_user)
    assert allowed is False
    assert secs > 0

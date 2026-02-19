"""Tests for balance: deduct_bet, credit_win, credit_referral_bonus, check_sufficient."""

from __future__ import annotations

import pytest

from bot.services.balance import check_sufficient, credit_deposit, credit_referral_bonus, credit_win, deduct_bet, deduct_withdraw, get_balance


@pytest.mark.asyncio
async def test_get_balance_real_and_demo(db, test_user: int) -> None:
    """get_balance returns real_balance when demo_mode=False, demo_balance when True."""
    from bot.database.queries import users as users_queries

    await users_queries.update_balance(test_user, real_balance=1000, demo_balance=2000)
    assert await get_balance(test_user, demo_mode=False) == 1000
    assert await get_balance(test_user, demo_mode=True) == 2000


@pytest.mark.asyncio
async def test_check_sufficient(db, test_user: int) -> None:
    """check_sufficient returns True when balance >= amount, False otherwise."""
    from bot.database.queries import users as users_queries

    await users_queries.update_balance(test_user, real_balance=500)
    assert await check_sufficient(test_user, 300, is_demo=False) is True
    assert await check_sufficient(test_user, 600, is_demo=False) is False


@pytest.mark.asyncio
async def test_deduct_bet_demo(db, test_user: int) -> None:
    """deduct_bet decreases demo_balance; does not go below 0."""
    from bot.database.queries import users as users_queries

    await users_queries.update_balance(test_user, demo_balance=100)
    await deduct_bet(test_user, 60, is_demo=True)
    row = await users_queries.get_user_balance(test_user)
    assert row is not None
    assert row.demo_balance == 40
    await deduct_bet(test_user, 100, is_demo=True)  # more than 40
    row = await users_queries.get_user_balance(test_user)
    assert row is not None
    assert row.demo_balance == 0


@pytest.mark.asyncio
async def test_deduct_bet_real(db, test_user: int) -> None:
    """deduct_bet decreases real_balance; does not go below 0."""
    from bot.database.queries import users as users_queries

    await users_queries.update_balance(test_user, real_balance=1000)
    await deduct_bet(test_user, 300, is_demo=False)
    row = await users_queries.get_user_balance(test_user)
    assert row is not None
    assert row.real_balance == 700


@pytest.mark.asyncio
async def test_credit_win_demo(db, test_user: int) -> None:
    """credit_win increases demo_balance."""
    from bot.database.queries import users as users_queries

    await users_queries.update_balance(test_user, demo_balance=100)
    await credit_win(test_user, 50, is_demo=True)
    row = await users_queries.get_user_balance(test_user)
    assert row is not None
    assert row.demo_balance == 150


@pytest.mark.asyncio
async def test_credit_win_real(db, test_user: int) -> None:
    """credit_win increases real_balance."""
    from bot.database.queries import users as users_queries

    await users_queries.update_balance(test_user, real_balance=500)
    await credit_win(test_user, 200, is_demo=False)
    row = await users_queries.get_user_balance(test_user)
    assert row is not None
    assert row.real_balance == 700


@pytest.mark.asyncio
async def test_credit_referral_bonus(db, test_user: int) -> None:
    """credit_referral_bonus increases real_balance only."""
    from bot.database.queries import users as users_queries

    await users_queries.update_balance(test_user, real_balance=0, demo_balance=1000)
    await credit_referral_bonus(test_user, 500)
    row = await users_queries.get_user_balance(test_user)
    assert row is not None
    assert row.real_balance == 500
    assert row.demo_balance == 1000


@pytest.mark.asyncio
async def test_credit_deposit(db, test_user: int) -> None:
    """credit_deposit increases real_balance."""
    from bot.database.queries import users as users_queries

    await users_queries.update_balance(test_user, real_balance=100)
    await credit_deposit(test_user, 1500)
    row = await users_queries.get_user_balance(test_user)
    assert row is not None
    assert row.real_balance == 1600


@pytest.mark.asyncio
async def test_deduct_withdraw(db, test_user: int) -> None:
    """deduct_withdraw decreases real_balance; does not go below 0."""
    from bot.database.queries import users as users_queries

    await users_queries.update_balance(test_user, real_balance=500)
    await deduct_withdraw(test_user, 200)
    row = await users_queries.get_user_balance(test_user)
    assert row is not None
    assert row.real_balance == 300
    await deduct_withdraw(test_user, 500)
    row = await users_queries.get_user_balance(test_user)
    assert row is not None
    assert row.real_balance == 0

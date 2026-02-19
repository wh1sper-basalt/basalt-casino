"""Balance operations: get, check, deduct bet, credit win, referral bonus."""

from __future__ import annotations

from bot.database.queries import users as users_queries


async def get_balance(user_id: int, demo_mode: bool) -> int:
    """Return current real_balance or demo_balance."""
    row = await users_queries.get_user_balance(user_id)
    if not row:
        return 0
    return row.demo_balance if demo_mode else row.real_balance


async def check_sufficient(user_id: int, amount: int, is_demo: bool) -> bool:
    """True if balance >= amount."""
    return await get_balance(user_id, is_demo) >= amount


async def deduct_bet(user_id: int, amount: int, is_demo: bool) -> None:
    """Decrease real_balance or demo_balance by amount."""
    row = await users_queries.get_user_balance(user_id)
    if not row:
        return
    if is_demo:
        new_balance = max(0, row.demo_balance - amount)
        await users_queries.update_balance(user_id, demo_balance=new_balance)
    else:
        new_balance = max(0, row.real_balance - amount)
        await users_queries.update_balance(user_id, real_balance=new_balance)


async def credit_win(user_id: int, amount: int, is_demo: bool) -> None:
    """Increase real_balance or demo_balance by amount."""
    row = await users_queries.get_user_balance(user_id)
    if not row:
        return
    if is_demo:
        await users_queries.update_balance(user_id, demo_balance=row.demo_balance + amount)
    else:
        await users_queries.update_balance(user_id, real_balance=row.real_balance + amount)


async def credit_referral_bonus(user_id: int, amount: int) -> None:
    """Increase real_balance by amount (referral bonus is always on real account)."""
    row = await users_queries.get_user_balance(user_id)
    if not row:
        return
    await users_queries.update_balance(user_id, real_balance=row.real_balance + amount)


async def credit_deposit(user_id: int, amount: int) -> None:
    """Increase real_balance by amount; call after approving deposit request."""
    row = await users_queries.get_user_balance(user_id)
    if not row:
        return
    await users_queries.update_balance(user_id, real_balance=row.real_balance + amount)


async def deduct_withdraw(user_id: int, amount: int) -> None:
    """Decrease real_balance by amount; call after approving withdraw request."""
    row = await users_queries.get_user_balance(user_id)
    if not row:
        return
    new_balance = max(0, row.real_balance - amount)
    await users_queries.update_balance(user_id, real_balance=new_balance)

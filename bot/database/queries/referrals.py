"""Referrals table queries."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from bot.database.connection import get_connection


async def add_referral(user_id: int, referrer_id: int) -> None:
    """Insert referral row (created_at = now, bonus_credited = 0). Ignores if user_id already exists."""
    conn = await get_connection()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    await conn.execute(
        "INSERT OR IGNORE INTO referrals (user_id, referrer_id, created_at, bonus_credited) VALUES (?, ?, ?, 0)",
        (user_id, referrer_id, now),
    )
    await conn.commit()


async def get_referrer_by_user(user_id: int) -> Optional[int]:
    """Return referrer_id for user or None."""
    conn = await get_connection()
    cursor = await conn.execute(
        "SELECT referrer_id FROM referrals WHERE user_id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    return int(row[0]) if row else None


async def count_referrals_by_referrer(referrer_id: int) -> int:
    """Count referrals for referrer."""
    conn = await get_connection()
    cursor = await conn.execute(
        "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?",
        (referrer_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    return int(row[0]) if row else 0


async def set_bonus_credited(user_id: int) -> None:
    """Set bonus_credited = 1 for this referred user."""
    conn = await get_connection()
    await conn.execute(
        "UPDATE referrals SET bonus_credited = 1 WHERE user_id = ?",
        (user_id,),
    )
    await conn.commit()


async def referral_exists(user_id: int) -> bool:
    """True if user already has a referral row."""
    conn = await get_connection()
    cursor = await conn.execute(
        "SELECT 1 FROM referrals WHERE user_id = ? LIMIT 1",
        (user_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    return row is not None

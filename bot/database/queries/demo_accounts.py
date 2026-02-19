"""Demo_accounts table queries."""

from __future__ import annotations

from typing import Optional

from bot.database.connection import get_connection
from bot.database.models import DemoAccount


async def get_demo_account(user_id: int) -> Optional[DemoAccount]:
    """Return demo_account row or None."""
    conn = await get_connection()
    cursor = await conn.execute(
        "SELECT user_id, last_reset, reset_count FROM demo_accounts WHERE user_id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    if not row:
        return None
    return DemoAccount(
        user_id=row[0],
        last_reset=row[1],
        reset_count=row[2],
    )


async def upsert_demo_reset(user_id: int, last_reset: str) -> None:
    """Set last_reset and increment reset_count. Assumes row exists (created with user)."""
    conn = await get_connection()
    await conn.execute(
        "UPDATE demo_accounts SET last_reset = ?, reset_count = reset_count + 1 WHERE user_id = ?",
        (last_reset, user_id),
    )
    await conn.commit()

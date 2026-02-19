"""User_stats table queries."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple

from bot.database.connection import get_connection
from bot.database.models import UserStats


async def get_or_create_stats(user_id: int) -> UserStats:
    """Return user_stats row; insert with zeros if missing."""
    conn = await get_connection()
    cursor = await conn.execute(
        "SELECT user_id, total_games, total_wins, total_losses, total_deposited, total_withdrawn, total_won, total_lost, last_updated " "FROM user_stats WHERE user_id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    if row:
        return UserStats(
            user_id=row[0],
            total_games=row[1],
            total_wins=row[2],
            total_losses=row[3],
            total_deposited=row[4],
            total_withdrawn=row[5],
            total_won=row[6],
            total_lost=row[7],
            last_updated=row[8],
        )
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    await conn.execute(
        "INSERT INTO user_stats (user_id, last_updated) VALUES (?, ?)",
        (user_id, now),
    )
    await conn.commit()
    return UserStats(user_id=user_id, last_updated=now)


async def update_stats_after_game(
    user_id: int,
    is_win: bool,
    bet_amount: int,
    win_amount: int,
) -> None:
    """Increment total_games; if win then total_wins and total_won, else total_losses and total_lost."""
    conn = await get_connection()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    await conn.execute(
        """
        UPDATE user_stats SET
            total_games = total_games + 1,
            total_wins = total_wins + ?,
            total_losses = total_losses + ?,
            total_won = total_won + ?,
            total_lost = total_lost + ?,
            last_updated = ?
        WHERE user_id = ?
        """,
        (
            1 if is_win else 0,
            0 if is_win else 1,
            win_amount,
            0 if is_win else bet_amount,
            now,
            user_id,
        ),
    )
    await conn.commit()


async def update_stats_after_payment(user_id: int, request_type: str, amount: int) -> None:
    """For approved payment: increase total_deposited or total_withdrawn."""
    conn = await get_connection()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if request_type == "deposit":
        await conn.execute(
            "UPDATE user_stats SET total_deposited = total_deposited + ?, last_updated = ? WHERE user_id = ?",
            (amount, now, user_id),
        )
    else:
        await conn.execute(
            "UPDATE user_stats SET total_withdrawn = total_withdrawn + ?, last_updated = ? WHERE user_id = ?",
            (amount, now, user_id),
        )
    await conn.commit()


async def get_aggregate_totals() -> Tuple[int, int]:
    """Return (sum of total_deposited, sum of total_withdrawn) across all users (for admin stats)."""
    conn = await get_connection()
    cursor = await conn.execute("SELECT COALESCE(SUM(total_deposited), 0), COALESCE(SUM(total_withdrawn), 0) FROM user_stats")
    row = await cursor.fetchone()
    await cursor.close()
    return (int(row[0]), int(row[1])) if row else (0, 0)


async def get_user_stats(user_id: int) -> Optional[UserStats]:
    """Get user stats by user_id. Returns None if not found."""
    conn = await get_connection()
    cursor = await conn.execute(
        "SELECT user_id, total_games, total_wins, total_losses, total_deposited, total_withdrawn, total_won, total_lost, last_updated " "FROM user_stats WHERE user_id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    if row:
        return UserStats(
            user_id=row[0],
            total_games=row[1],
            total_wins=row[2],
            total_losses=row[3],
            total_deposited=row[4],
            total_withdrawn=row[5],
            total_won=row[6],
            total_lost=row[7],
            last_updated=row[8],
        )
    return None

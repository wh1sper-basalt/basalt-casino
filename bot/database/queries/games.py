"""Games table queries."""

from __future__ import annotations

from typing import List

from bot.database.connection import get_connection
from bot.database.models import Game


async def save_game(
    user_id: int,
    game_type: str,
    game_id: int,
    bet_amount: int,
    outcome: str,
    is_win: bool,
    win_amount: int,
    is_demo: bool,
    played_at: str,
) -> None:
    """Insert one game record."""
    conn = await get_connection()
    await conn.execute(
        """
        INSERT INTO games (user_id, game_type, game_id, bet_amount, outcome, is_win, win_amount, is_demo, played_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            game_type,
            game_id,
            bet_amount,
            outcome,
            1 if is_win else 0,
            win_amount,
            1 if is_demo else 0,
            played_at,
        ),
    )
    await conn.commit()


async def get_last_games_by_user(user_id: int, limit: int = 10) -> List[Game]:
    """Return last `limit` games for user (by played_at DESC)."""
    conn = await get_connection()
    cursor = await conn.execute(
        """
        SELECT id, user_id, game_type, game_id, bet_amount, outcome, is_win, win_amount, is_demo, played_at
        FROM games WHERE user_id = ? ORDER BY played_at DESC LIMIT ?
        """,
        (user_id, limit),
    )
    rows = await cursor.fetchall()
    await cursor.close()
    return [
        Game(
            id=r[0],
            user_id=r[1],
            game_type=r[2],
            game_id=r[3],
            bet_amount=r[4],
            outcome=r[5],
            is_win=bool(r[6]),
            win_amount=r[7],
            is_demo=bool(r[8]),
            played_at=r[9],
        )
        for r in rows
    ]


async def get_games_count(user_id: int | None = None) -> int:
    """Return total games count, optionally for one user."""
    conn = await get_connection()
    if user_id is not None:
        cursor = await conn.execute("SELECT COUNT(*) FROM games WHERE user_id = ?", (user_id,))
    else:
        cursor = await conn.execute("SELECT COUNT(*) FROM games")
    row = await cursor.fetchone()
    await cursor.close()
    return int(row[0]) if row else 0


async def get_total_bet_by_user(user_id: int) -> int:
    """Get sum of all bet amounts for a user."""
    conn = await get_connection()
    cursor = await conn.execute(
        "SELECT COALESCE(SUM(bet_amount), 0) FROM games WHERE user_id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    return int(row[0]) if row else 0

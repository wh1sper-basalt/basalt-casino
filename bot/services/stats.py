"""Stats calculation services for admin panel."""

from __future__ import annotations

from bot.database.queries import user_stats as stats_queries


async def get_user_stats_display(user_id: int) -> dict:
    """Get user stats formatted for display in admin panel."""
    stats = await stats_queries.get_user_stats(user_id)

    if not stats:
        return {
            "total_games": 0,
            "total_wins": 0,
            "total_losses": 0,
            "win_rate": 0.0,
            "total_deposited": 0,
            "total_withdrawn": 0,
            "total_won": 0,
            "total_lost": 0,
        }

    # Calculate win rate
    total_games = stats.total_games
    win_rate = 0.0
    if total_games > 0:
        win_rate = round((stats.total_wins / total_games * 100), 2)

    return {
        "total_games": stats.total_games,
        "total_wins": stats.total_wins,
        "total_losses": stats.total_losses,
        "win_rate": win_rate,
        "total_deposited": stats.total_deposited,
        "total_withdrawn": stats.total_withdrawn,
        "total_won": stats.total_won,
        "total_lost": stats.total_lost,
    }

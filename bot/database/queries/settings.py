"""Settings (singleton) queries."""

from __future__ import annotations

from bot.database.connection import get_connection
from bot.database.models import Settings


async def get_settings() -> Settings:
    """Return the single settings row (id=1)."""
    conn = await get_connection()
    cursor = await conn.execute(
        "SELECT id, min_bet, max_bet, win_coefficient, referral_bonus, demo_balance, "
        "deposit_commission, tech_works_global, tech_works_demo, tech_works_real, updated_at "
        "FROM settings WHERE id = 1"
    )
    row = await cursor.fetchone()
    await cursor.close()
    if not row:
        raise RuntimeError("Settings row missing. Run migrations.")
    return Settings(
        id=row[0],
        min_bet=row[1],
        max_bet=row[2],
        win_coefficient=row[3],
        referral_bonus=row[4],
        demo_balance=row[5],
        deposit_commission=row[6] or 0.0,
        tech_works_global=row[7],
        tech_works_demo=row[8],
        tech_works_real=row[9],
        updated_at=row[10],
    )


async def update_settings(**kwargs: object) -> None:
    """Update settings fields. updated_at set to now."""
    if not kwargs:
        return
    conn = await get_connection()
    allowed = {
        "min_bet",
        "max_bet",
        "win_coefficient",
        "referral_bonus",
        "demo_balance",
        "deposit_commission",
        "tech_works_global",
        "tech_works_demo",
        "tech_works_real",
    }
    sets = ["updated_at = datetime('now')"]
    values = []
    for k, v in kwargs.items():
        if k in allowed:
            sets.append(f"{k} = ?")
            values.append(v)
    if len(values) == 0:
        return
    values.append(1)
    await conn.execute(
        f"UPDATE settings SET {', '.join(sets)} WHERE id = ?",
        tuple(values),
    )
    await conn.commit()

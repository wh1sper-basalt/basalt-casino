"""Pytest fixtures: in-memory SQLite, migrations, test user and settings."""

from __future__ import annotations

import aiosqlite
import pytest_asyncio

from bot.core.constants import BOT_DIR


@pytest_asyncio.fixture
async def db(monkeypatch):
    """
    In-memory SQLite with 001_initial.sql applied and default settings row.
    Patches bot.database.connection._connection so all queries use this DB.
    """
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")

    migrations_dir = BOT_DIR / "database" / "migrations"
    sql_path = migrations_dir / "001_initial.sql"
    sql = sql_path.read_text(encoding="utf-8")
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if not stmt or stmt.startswith("--"):
            continue
        await conn.execute(stmt)

    # Force add contact columns for tests
    try:
        await conn.execute("ALTER TABLE users ADD COLUMN has_contact_sent INTEGER NOT NULL DEFAULT 0")
        await conn.execute("ALTER TABLE users ADD COLUMN contact_phone TEXT")
        await conn.commit()
    except Exception:
        # Columns might already exist
        pass

    await conn.execute(
        """
        INSERT OR IGNORE INTO settings (
            id, min_bet, max_bet, win_coefficient, referral_bonus, demo_balance,
            deposit_commission, tech_works_global, tech_works_demo, tech_works_real, updated_at
        ) VALUES (
            1, 100, 100000, 1.8, 500, 50000,
            0.0, 0, 0, 0, datetime('now')
        )
        """
    )
    await conn.commit()

    import bot.database.connection as conn_module

    monkeypatch.setattr(conn_module, "_connection", conn)
    yield conn
    await conn.close()
    monkeypatch.setattr(conn_module, "_connection", None)


@pytest_asyncio.fixture
async def test_user(db):
    """Create one test user (user_id=1000) with balances and stats. Requires db fixture."""
    from bot.database.queries import users as users_queries

    await users_queries.create_user(
        user_id=1000,
        username="testuser",
        first_name="Test",
        last_name="User",
        full_name="Test User",
    )
    return 1000


@pytest_asyncio.fixture
async def test_user_and_referrer(db):
    """Create referrer 2000 and referred user 1000. Requires db fixture."""
    from bot.database.queries import users as users_queries

    for uid, uname in [(2000, "referrer"), (1000, "referred")]:
        await users_queries.create_user(
            user_id=uid,
            username=uname,
            first_name="U",
            last_name="",
            full_name="U",
        )
    return 1000, 2000

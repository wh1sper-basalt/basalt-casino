"""aiosqlite connection and migration runner."""

from __future__ import annotations

import asyncio
import os
import sqlite3
import sys
from pathlib import Path
from typing import Optional

import aiosqlite

from bot.core.constants import BOT_DIR
from bot.utils.logger import get_logger

log = get_logger(__name__)

_connection: Optional[aiosqlite.Connection] = None


def _get_database_path(db_path: Optional[str] = None) -> str:
    """Return db path: argument > env DATABASE_PATH > config > default."""
    if db_path:
        return db_path
    path = os.environ.get("DATABASE_PATH", "").strip()
    if path:
        return path
    try:
        from bot.config import get_config

        return get_config().database_path
    except Exception:
        return "./data/database2.db"


async def get_connection() -> aiosqlite.Connection:
    """Return the global DB connection. Call init_db() first."""
    if _connection is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _connection


async def init_db(db_path: Optional[str] = None) -> None:
    """
    Open database, run migrations (001_initial.sql), insert default settings if missing.
    Sets global _connection.
    """
    global _connection
    path = _get_database_path(db_path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    try:
        _connection = await aiosqlite.connect(path)
    except sqlite3.DatabaseError as e:
        if "malformed" in str(e).lower():
            log.error(
                "Database file is corrupted: %s. Rename or remove the file and restart to create a new DB.",
                path,
            )
        raise
    _connection.row_factory = aiosqlite.Row
    await _connection.execute("PRAGMA foreign_keys = ON")

    migrations_dir = BOT_DIR / "database" / "migrations"
    version = await _get_schema_version()
    if version < 1:
        await _run_initial_sql(migrations_dir / "001_initial.sql")
        await _insert_default_settings()
        log.info("Applied migration 001_initial, inserted default settings")
    if version < 2:
        await _run_initial_sql(migrations_dir / "002_user_contact.sql")
        await _connection.execute("INSERT INTO schema_version (version, applied_at) VALUES (2, datetime('now'))")
        await _connection.commit()
        log.info("Applied migration 002_user_contact")


async def _get_schema_version() -> int:
    """Return current schema_version or 0 if table missing."""
    try:
        cursor = await _connection.execute("SELECT MAX(version) FROM schema_version")
        row = await cursor.fetchone()
        await cursor.close()
        return int(row[0]) if row and row[0] is not None else 0
    except aiosqlite.OperationalError:
        return 0


async def _run_initial_sql(file_path: Path) -> None:
    sql = file_path.read_text(encoding="utf-8")
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for stmt in statements:
        await _connection.execute(stmt)
    await _connection.commit()


async def _insert_default_settings() -> None:
    await _connection.execute(
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
    await _connection.commit()


async def close_db() -> None:
    """Close the global connection."""
    global _connection
    if _connection is not None:
        await _connection.close()
        _connection = None
        log.info("Database connection closed")


def _run_migrate() -> None:
    """CLI: run migrations (make migrate)."""
    asyncio.run(init_db())
    asyncio.run(close_db())


if __name__ == "__main__":
    _run_migrate()
    sys.exit(0)

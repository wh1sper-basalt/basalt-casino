"""Backup and cleanup: monthly dump (1st of month), keep 3 dumps, purge old games and payment_requests."""

from __future__ import annotations

import asyncio
import gzip
import sqlite3
from datetime import date
from pathlib import Path

from bot.core.constants import GAME_HISTORY_DAYS, MAX_DUMPS_KEEP, PAYMENT_REQUESTS_DAYS
from bot.database.connection import get_connection
from bot.utils.logger import get_logger

log = get_logger(__name__)


def _do_dump_sync(db_path: str, dump_path: Path) -> None:
    """Run sqlite3 dump and gzip to dump_path (blocking). Uses separate connection."""
    conn = sqlite3.connect(db_path)
    try:
        with gzip.open(dump_path, "wt", encoding="utf-8") as f:
            for line in conn.iterdump():
                f.write(line + "\n")
    finally:
        conn.close()


async def run_backup_and_cleanup(db_path: str, backups_dir: str) -> None:
    """
    If today is the 1st of the month: create gzipped dump in backups_dir (casino_YYYY-MM-DD.gz).
    Keep only the last MAX_DUMPS_KEEP dumps.
    Delete from games where played_at older than GAME_HISTORY_DAYS.
    Delete from payment_requests where status in ('approved','rejected') and created_at older than PAYMENT_REQUESTS_DAYS.
    """
    backups_path = Path(backups_dir)
    backups_path.mkdir(parents=True, exist_ok=True)
    today = date.today()

    if today.day == 1:
        dump_name = f"casino_{today.isoformat()}.gz"
        dump_path = backups_path / dump_name
        try:
            await asyncio.to_thread(_do_dump_sync, db_path, dump_path)
            log.info("Backup created: %s", dump_path)
        except Exception as e:
            log.error("Backup failed: %s", e)
            return

        existing = sorted(backups_path.glob("casino_*.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in existing[MAX_DUMPS_KEEP:]:
            try:
                old.unlink()
                log.info("Removed old dump: %s", old)
            except OSError as e:
                log.warning("Could not remove %s: %s", old, e)

    conn = await get_connection()
    try:
        cur_games = await conn.execute(
            "DELETE FROM games WHERE played_at < datetime('now', ?)",
            (f"-{GAME_HISTORY_DAYS} days",),
        )
        deleted_games = cur_games.rowcount
        await cur_games.close()
        cur_payments = await conn.execute(
            "DELETE FROM payment_requests WHERE status IN ('approved', 'rejected') AND created_at < datetime('now', ?)",
            (f"-{PAYMENT_REQUESTS_DAYS} days",),
        )
        deleted_payments = cur_payments.rowcount
        await cur_payments.close()
        await conn.commit()
        if deleted_games or deleted_payments:
            log.info("Cleanup: deleted %s games, %s payment_requests", deleted_games, deleted_payments)
    except Exception as e:
        log.error("Cleanup failed: %s", e)


async def _run_once() -> None:
    """Load config, init_db, run backup and cleanup, close_db. For CLI invocation."""
    from bot.config import get_config
    from bot.database.connection import close_db, init_db

    config = get_config()
    db_path = config.database_path
    backups_dir = str(Path(db_path).resolve().parent.parent / "backups")
    await init_db()
    try:
        await run_backup_and_cleanup(db_path, backups_dir)
    finally:
        await close_db()


if __name__ == "__main__":
    import sys

    asyncio.run(_run_once())
    sys.exit(0)

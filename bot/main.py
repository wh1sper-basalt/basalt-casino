"""Single entry point: create bot, register middlewares and routers, run polling."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_config
from bot.core.constants import IMAGES_DIR
from bot.database.connection import close_db, init_db
from bot.handlers import get_root_router
from bot.middlewares import BotInjectMiddleware, CurrencyMiddleware, DemoRestoreMiddleware, LoggingMiddleware, TechWorkMiddleware, UserBlockMiddleware
from bot.utils.backup import run_backup_and_cleanup
from bot.utils.logger import get_logger, setup_logger

log = get_logger(__name__)

BACKUP_INTERVAL_SECONDS = 86400


async def _backup_loop(db_path: str, backups_dir: str) -> None:
    """Every 24h run backup and cleanup."""
    while True:
        await asyncio.sleep(BACKUP_INTERVAL_SECONDS)
        try:
            await run_backup_and_cleanup(db_path, backups_dir)
        except asyncio.CancelledError:
            break
        except Exception as e:
            log.exception("Backup task error: %s", e)


async def main() -> None:
    """Run bot: load config, setup logger, init DB, create bot and dispatcher, start polling."""
    config = get_config()
    setup_logger()
    log.info("Starting bot")
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    (IMAGES_DIR / "en").mkdir(exist_ok=True)
    (IMAGES_DIR / "ru").mkdir(exist_ok=True)
    log.info(
        "Images: %s/en/ and %s/ru/ (place basalt_<screen>.png in each)",
        IMAGES_DIR.resolve(),
        IMAGES_DIR.resolve(),
    )

    await init_db()
    db_path = config.database_path
    backups_dir = str(Path(db_path).resolve().parent.parent / "backups")
    backup_task = asyncio.create_task(_backup_loop(db_path, backups_dir))

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(BotInjectMiddleware(bot))
    dp.update.outer_middleware(CurrencyMiddleware())
    dp.update.outer_middleware(TechWorkMiddleware())
    dp.update.outer_middleware(UserBlockMiddleware())
    dp.update.outer_middleware(DemoRestoreMiddleware())
    dp.update.outer_middleware(LoggingMiddleware())
    dp.include_router(get_root_router())
    try:
        await dp.start_polling(bot)
    finally:
        backup_task.cancel()
        try:
            await backup_task
        except asyncio.CancelledError:
            pass
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped.")
        sys.exit(0)

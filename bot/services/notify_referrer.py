"""Notify referrer when someone uses their referral link."""

from __future__ import annotations

from aiogram.types import FSInputFile

from bot.database.queries import users as users_queries
from bot.templates.texts import get_text
from bot.utils.helpers import get_image_path
from bot.utils.logger import get_logger

log = get_logger(__name__)


async def notify_referrer_new_referral(
    bot,
    referrer_id: int,
    new_user_id: int,
    new_username: str | None,
    new_first_name: str | None,
) -> None:
    """Send notification to referrer about new referral."""
    try:
        referrer = await users_queries.get_user(referrer_id)
        if not referrer or not referrer.notifications_enabled:
            return

        lang = referrer.language or "en"

        # Format username for display
        username_display = f"@{new_username}" if new_username else new_first_name or f"user_{new_user_id}"

        caption = get_text("referrer_notification", lang, username=username_display)

        path = get_image_path("referral_notification", lang)

        if path.exists():
            await bot.send_photo(referrer_id, FSInputFile(str(path)), caption=caption)
        else:
            await bot.send_message(referrer_id, caption)

    except Exception as e:
        log.warning(f"Failed to notify referrer {referrer_id}: {e}")

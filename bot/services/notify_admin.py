"""Notify admins (e.g. new payment request in PM with Approve/Reject/Read)."""

from __future__ import annotations

import html

from aiogram.enums import ParseMode
from aiogram.types import FSInputFile

from bot.config import get_config
from bot.database.queries import users as users_queries
from bot.keyboards.inline import admin_new_request_notification_keyboard
from bot.templates.texts import get_text
from bot.utils.helpers import get_image_path
from bot.utils.logger import get_logger

log = get_logger(__name__)


async def notify_admins_new_payment_request(
    bot,
    request_id: int,
    request_type: str,
    amount: int,
    user_id: int,
    created_at: str,
) -> None:
    """
    Send to each admin a photo (basalt_newapplication.png) with contact info and Approve/Reject/Read.
    Uses each admin's language; caption is HTML-formatted (line breaks via <br>).
    """
    app_user = await users_queries.get_user(user_id)
    username = f"@{app_user.username}" if app_user and app_user.username else "—"
    phone = (app_user.contact_phone or "—") if app_user else "—"
    username = html.escape(str(username))
    phone = html.escape(str(phone))
    config = get_config()
    admin_ids = config.get_admin_ids()
    path_ru = get_image_path("newapplication", "ru")
    path_en = get_image_path("newapplication", "en")
    path = path_ru if path_ru.exists() else path_en
    for admin_id in admin_ids:
        try:
            admin_user = await users_queries.get_user(admin_id)
            lang = admin_user.language if admin_user else "ru"
            caption = get_text(
                "admin_new_request_caption",
                lang,
                request_id=request_id,
                request_type=request_type,
                amount=amount,
                user_id=user_id,
                username=username,
                phone=phone,
                created_at=created_at,
            )
            kb = admin_new_request_notification_keyboard(request_id, lang)
            if path.exists():
                await bot.send_photo(
                    admin_id,
                    FSInputFile(str(path)),
                    caption=caption,
                    reply_markup=kb,
                    parse_mode=ParseMode.HTML,
                )
            else:
                await bot.send_message(
                    admin_id,
                    caption,
                    reply_markup=kb,
                    parse_mode=ParseMode.HTML,
                )
        except Exception as e:
            log.warning("Failed to notify admin {} of new request {}: {}", admin_id, request_id, e)

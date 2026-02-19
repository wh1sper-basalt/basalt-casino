"""Command /start: referral handling, user creation, welcome/home image, main menu."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, Message

from bot.database.queries import users as users_queries
from bot.keyboards.inline import main_menu
from bot.services.notify_referrer import notify_referrer_new_referral
from bot.services.referral import generate_referral_link, process_referral_bonuses, validate_referral_link
from bot.templates.texts import get_text
from bot.utils.helpers import get_image_path
from bot.utils.logger import get_logger

log = get_logger(__name__)
router = Router(name="start")


@router.message(CommandStart(), lambda m: m.text is not None)
async def cmd_start(message: Message) -> None:
    """
    Handle /start. Parse deep_link for referral; create user on first run;
    apply referral bonuses if valid; send welcome/home image + text + main menu; delete command.
    """
    user = message.from_user
    if not user:
        return
    user_id = user.id
    text = message.text or ""
    args = text.split(maxsplit=1)
    ref_code = args[1].strip() if len(args) > 1 else None

    referrer_id = None
    if ref_code:
        referrer_id = validate_referral_link(ref_code)

    existing = await users_queries.get_user(user_id)
    is_first = existing is None

    if is_first:
        # Получаем username бота
        bot_username = (await message.bot.me()).username

        # Генерируем реферальную ссылку
        referral_code = generate_referral_link(user_id, bot_username)

        full_name = (user.first_name or "") + (" " + (user.last_name or "") if user.last_name else "")
        await users_queries.create_user(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name or "",
            last_name=user.last_name,
            full_name=full_name.strip(),
            referral_link=referral_code,  # ← добавляем ссылку
        )

        if referrer_id is not None:
            await process_referral_bonuses(user_id, referrer_id)
            await notify_referrer_new_referral(message.bot, referrer_id, user_id, user.username, user.first_name)

    user_after = await users_queries.get_user(user_id)
    lang = user_after.language if user_after else "en"
    caption = get_text("welcome_first", lang) if is_first else get_text("welcome_return", lang)
    screen = "welcome" if is_first else "home"
    img_path = get_image_path(screen, lang)
    kb = main_menu(lang)

    try:
        if img_path.exists():
            photo = FSInputFile(str(img_path))
            await message.answer_photo(photo=photo, caption=caption, reply_markup=kb)
        else:
            log.warning("Image not found: %s (add basalt_%s.png in images/%s/)", img_path, screen, lang)
            await message.answer(caption, reply_markup=kb)
    except Exception as e:
        log.warning("Image send failed, fallback to text: {}", e)
        await message.answer(caption, reply_markup=kb)

    try:
        await message.delete()
    except Exception:
        pass

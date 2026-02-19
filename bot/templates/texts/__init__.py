"""i18n: get_text(key, lang) from ru/en dicts."""

from __future__ import annotations

from bot.core.constants import DEFAULT_LANGUAGE
from bot.templates.texts import en, ru

_LANGS = {"en": en.TEXTS, "ru": ru.TEXTS}


def get_text(key: str, lang: str = DEFAULT_LANGUAGE, **format_kwargs: object) -> str:
    """
    Return phrase by key for lang ('en' or 'ru'). Fallback to en if key or lang missing.
    Use **format_kwargs for .format() if needed.
    """
    texts = _LANGS.get(lang) or _LANGS["en"]
    raw = texts.get(key) or _LANGS["en"].get(key) or key
    if format_kwargs:
        return str(raw).format(**format_kwargs)
    return str(raw)

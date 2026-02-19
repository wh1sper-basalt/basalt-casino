"""Helpers: image path, formatting (no project-specific logic)."""

from __future__ import annotations

from pathlib import Path

from bot.core.constants import IMAGES_DIR


def get_image_path(screen: str, lang: str) -> Path:
    """Return path to template image: templates/images/{lang}/basalt_{screen}.png or .jpg (png preferred)."""
    folder = (IMAGES_DIR / lang).resolve()
    for ext in (".png", ".jpg"):
        p = folder / f"basalt_{screen}{ext}"
        if p.exists():
            return p
    return folder / f"basalt_{screen}.png"


def format_amount(amount: int) -> str:
    """Format amount with thousands separator and currency (e.g. 1 500 ₽)."""
    return f"{amount:,}".replace(",", " ") + " ₽"


def seconds_to_hours_minutes(seconds: int) -> str:
    """Format seconds as 'X h Y min' for demo restore cooldown message."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    if h > 0 and m > 0:
        return f"{h} h {m} min"
    if h > 0:
        return f"{h} h"
    return f"{m} min"

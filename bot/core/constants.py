"""Immutable constants: paths, retention limits, default language, currency."""

from pathlib import Path

# Paths (relative to project root when running from root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BOT_DIR = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = BOT_DIR / "templates"
IMAGES_DIR = TEMPLATES_DIR / "images"
TEXTS_DIR = TEMPLATES_DIR / "texts"

# Backup and cleanup
MAX_DUMPS_KEEP = 3
GAME_HISTORY_DAYS = 30
PAYMENT_REQUESTS_DAYS = 14

# Demo restore: next restore allowed after this many seconds
DEMO_RESTORE_INTERVAL_SECONDS = 24 * 3600

# Locale and display
DEFAULT_LANGUAGE = "en"
CURRENCY = "₽"

# Telegram dice emoji types (for GAME_LIST mapping)
GAME_EMOJI_TYPES = (
    "dice",
    "darts",
    "basketball",
    "football",
    "bowling",
    "slot_machine",
)

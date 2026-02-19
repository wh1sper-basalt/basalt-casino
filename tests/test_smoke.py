"""Smoke tests so CI has at least one test."""


def test_import_bot_main() -> None:
    """Bot main module can be imported."""
    import bot.main  # noqa: F401

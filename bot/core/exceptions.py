"""Domain exceptions: handlers catch and convert to user messages."""


class InsufficientFunds(Exception):
    """User balance is less than required amount."""


class GameNotAvailable(Exception):
    """Game or outcome is not available (e.g. tech works)."""


class UserBlocked(Exception):
    """User is blocked (full or partial)."""


class DemoRestoreNotAvailable(Exception):
    """Demo restore not allowed yet (e.g. 24h not passed)."""


class InvalidReferralLink(Exception):
    """Referral link is invalid or tampered."""

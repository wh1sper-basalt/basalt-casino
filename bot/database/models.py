"""Pydantic models for DB rows (no ORM)."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    """User row from users table."""

    user_id: int
    username: Optional[str] = None
    first_name: str = ""
    last_name: Optional[str] = None
    full_name: str = ""
    referral_link: Optional[str] = None
    created_at: str
    is_blocked: int = 0
    block_type: Optional[str] = None
    language: str = "en"
    has_contact_sent: int = 0
    contact_phone: Optional[str] = None
    notifications_enabled: int = 1
    fast_mode: int = 0


class UserBalance(BaseModel):
    """Row from user_balances."""

    user_id: int
    real_balance: int = 0
    demo_balance: int = 0
    demo_mode: int = 1


class Referral(BaseModel):
    """Row from referrals."""

    id: int
    user_id: int
    referrer_id: int
    created_at: str
    bonus_credited: int = 0


class DemoAccount(BaseModel):
    """Row from demo_accounts."""

    user_id: int
    last_reset: Optional[str] = None
    reset_count: int = 0


class Game(BaseModel):
    """Row from games."""

    id: int
    user_id: int
    game_type: str
    game_id: int
    bet_amount: int
    outcome: str
    is_win: int
    win_amount: int
    is_demo: int
    played_at: str


class PaymentRequest(BaseModel):
    """Row from payment_requests."""

    id: int
    user_id: int
    request_type: str
    amount: int
    status: str
    payment_method: Optional[str] = None
    payment_details: Optional[str] = None
    created_at: str
    processed_at: Optional[str] = None
    processed_by: Optional[int] = None


class Settings(BaseModel):
    """Single row from settings (id=1)."""

    id: int = 1
    min_bet: int
    max_bet: int
    win_coefficient: float
    referral_bonus: int
    demo_balance: int
    deposit_commission: float = 0.0
    tech_works_global: int = 0
    tech_works_demo: int = 0
    tech_works_real: int = 0
    updated_at: str


class UserStats(BaseModel):
    """Row from user_stats."""

    user_id: int
    total_games: int = 0
    total_wins: int = 0
    total_losses: int = 0
    total_deposited: int = 0
    total_withdrawn: int = 0
    total_won: int = 0
    total_lost: int = 0
    last_updated: str

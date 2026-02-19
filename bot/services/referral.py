"""Referral: signed link generation/validation, bonus processing."""
from __future__ import annotations

import base64
import hashlib
import secrets
import binascii
from typing import Optional

from bot.database.queries import referrals as referrals_queries
from bot.database.queries import settings as settings_queries
from bot.database.queries import users as users_queries
from bot.services.balance import credit_referral_bonus


def generate_referral_link(user_id: int, bot_username: str) -> str:
    """
    Build signed start parameter for referral link.
    payload = f"{user_id}:{salt}:{md5(f'{user_id}:{salt}')[:6]}", base64.urlsafe_b64encode.
    Returns only the payload string (to use as ?start=... or in users.referral_link).
    """
    salt = secrets.token_hex(4)
    raw = f"{user_id}:{salt}"
    signature = hashlib.md5(raw.encode()).hexdigest()[:6]
    payload = f"{user_id}:{salt}:{signature}"
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def validate_referral_link(link: str) -> Optional[int]:
    """
    Decode base64, verify md5 signature, return referrer_id (user_id of the one who shared).
    Returns None if invalid or tampered.
    """
    try:
        # Fix padding correctly
        link = link.strip()
        missing_padding = len(link) % 4
        if missing_padding:
            link += '=' * (4 - missing_padding)
        
        # Decode
        decoded = base64.urlsafe_b64decode(link)
        payload = decoded.decode('utf-8')
        
        # Split
        parts = payload.split(":")
        if len(parts) != 3:
            return None
        
        referrer_id = int(parts[0])
        salt = parts[1]
        sig = parts[2]
        
        # Verify signature
        raw = f"{referrer_id}:{salt}"
        expected = hashlib.md5(raw.encode()).hexdigest()[:6]
        
        # CRITICAL: String comparison must be exact
        if sig != expected:
            return None
            
        return referrer_id
        
    except (binascii.Error, UnicodeDecodeError, ValueError, TypeError):
        return None
    except Exception:
        return None


async def process_referral_bonuses(user_id: int, referrer_id: int) -> bool:
    """
    Check: user_id != referrer_id; referrer not blocked; no existing referral for user_id.
    Then add referral row, credit referral_bonus (from settings) to both, set bonus_credited=1.
    Returns True if bonuses were applied, False otherwise.
    """
    if user_id == referrer_id:
        return False
    referrer = await users_queries.get_user(referrer_id)
    if not referrer or referrer.is_blocked:
        return False
    if await referrals_queries.referral_exists(user_id):
        return False
    settings = await settings_queries.get_settings()
    amount = settings.referral_bonus
    await referrals_queries.add_referral(user_id, referrer_id)
    await credit_referral_bonus(user_id, amount)
    await credit_referral_bonus(referrer_id, amount)
    await referrals_queries.set_bonus_credited(user_id)
    return True
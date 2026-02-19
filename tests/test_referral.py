"""Tests for referral link generation, validation, bonus processing."""

from __future__ import annotations

import pytest

from bot.services.referral import (
    generate_referral_link,
    process_referral_bonuses,
    validate_referral_link,
)


def test_generate_and_validate_roundtrip() -> None:
    """A link generated for a user can be validated back to the same user_id."""
    user_id = 100
    link = generate_referral_link(user_id, "TestBot")
    result = validate_referral_link(link)
    assert result == user_id


def test_validate_tampered_returns_none() -> None:
    """Tampered payload or wrong signature returns None."""
    user_id = 100
    link = generate_referral_link(user_id, "TestBot")

    # Try multiple tampering methods
    tampered_links = [
        link + "A",  # Add character
        link[:-1],  # Remove character
        link[:-1] + ("X" if link[-1] != "X" else "Y"),  # Change one character
        link.replace(link[5], "X") if len(link) > 5 else link,  # Change middle character
        "A" + link[1:],  # Change first character
    ]

    for bad_link in tampered_links:
        result = validate_referral_link(bad_link)
        assert result is None, f"Link {bad_link} should be invalid but returned {result}"


@pytest.mark.asyncio
async def test_validate_own_link_rejected_in_process(db, test_user_and_referrer: tuple[int, int]) -> None:
    """process_referral_bonuses should reject when user tries to use own link."""
    user_id, _ = test_user_and_referrer
    result = await process_referral_bonuses(user_id, user_id)
    assert result is False


@pytest.mark.asyncio
async def test_process_referral_bonuses_credits_once(db, test_user_and_referrer: tuple[int, int]) -> None:
    """process_referral_bonuses credits both users; second call for same user does not credit again."""
    from bot.database.queries import users as users_queries

    user_id, referrer_id = test_user_and_referrer

    # First call should succeed
    ok = await process_referral_bonuses(user_id, referrer_id)
    assert ok is True

    # Check balances increased
    user_balance = await users_queries.get_user_balance(user_id)
    referrer_balance = await users_queries.get_user_balance(referrer_id)
    assert user_balance.real_balance == 500
    assert referrer_balance.real_balance == 500

    # Second call should fail
    ok2 = await process_referral_bonuses(user_id, referrer_id)
    assert ok2 is False


@pytest.mark.asyncio
async def test_process_referral_referrer_blocked(db) -> None:
    """process_referral_bonuses returns False when referrer is blocked."""
    from bot.database.queries import users as users_queries

    # Create users
    await users_queries.create_user(2000, "ref", "R", None, "R")
    await users_queries.create_user(1000, "usr", "U", None, "U")

    # Block referrer
    await users_queries.set_block(2000, True, "full")

    # Try to process referral
    ok = await process_referral_bonuses(1000, 2000)
    assert ok is False

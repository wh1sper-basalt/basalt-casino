"""User and user_balances queries."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from bot.database.connection import get_connection
from bot.database.models import User, UserBalance


async def get_user(user_id: int) -> Optional[User]:
    """Return user by user_id or None."""
    conn = await get_connection()
    cursor = await conn.execute(
        "SELECT user_id, username, first_name, last_name, full_name, referral_link, "
        "created_at, is_blocked, block_type, language, notifications_enabled, fast_mode, "
        "has_contact_sent, contact_phone FROM users WHERE user_id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    if not row:
        return None
    # has_contact_sent: DB can have NULL; normalize to 0/1
    raw_contact = row[12] if len(row) > 12 else None
    has_contact_sent = 1 if raw_contact == 1 else 0
    # contact_phone: can be NULL in DB
    contact_phone = row[13] if len(row) > 13 else None
    if contact_phone is not None and isinstance(contact_phone, str) and contact_phone.strip() == "":
        contact_phone = None

    return User(
        user_id=row[0],
        username=row[1],
        first_name=row[2] or "",
        last_name=row[3],
        full_name=row[4] or "",
        referral_link=row[5],
        created_at=row[6],
        is_blocked=row[7],
        block_type=row[8],
        language=row[9] or "en",
        notifications_enabled=row[10],
        fast_mode=row[11],
        has_contact_sent=has_contact_sent,
        contact_phone=contact_phone,
    )


async def get_user_balance(user_id: int) -> Optional[UserBalance]:
    """Return user_balances row by user_id or None."""
    conn = await get_connection()
    cursor = await conn.execute(
        "SELECT user_id, real_balance, demo_balance, demo_mode FROM user_balances WHERE user_id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    if not row:
        return None
    return UserBalance(user_id=row[0], real_balance=row[1], demo_balance=row[2], demo_mode=row[3])


async def create_user(
    user_id: int,
    username: Optional[str],
    first_name: str,
    last_name: Optional[str],
    full_name: str,
    referral_link: Optional[str] = None,
) -> None:
    """Insert user and related rows in user_balances, demo_accounts, user_stats."""
    conn = await get_connection()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    await conn.execute(
        """
        INSERT INTO users (user_id, username, first_name, last_name, full_name, referral_link, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, username, first_name, last_name, full_name, referral_link, now),
    )
    await conn.execute(
        "INSERT INTO user_balances (user_id) VALUES (?)",
        (user_id,),
    )
    await conn.execute(
        "INSERT INTO demo_accounts (user_id) VALUES (?)",
        (user_id,),
    )
    await conn.execute(
        "INSERT INTO user_stats (user_id, last_updated) VALUES (?, ?)",
        (user_id, now),
    )
    await conn.commit()


async def update_user(user_id: int, **kwargs: str | int | None) -> None:
    """Update user fields. Valid keys: username, first_name, last_name, full_name, language, notifications_enabled, fast_mode, referral_link."""
    if not kwargs:
        return
    conn = await get_connection()
    allowed = {
        "username",
        "first_name",
        "last_name",
        "full_name",
        "language",
        "notifications_enabled",
        "fast_mode",
        "referral_link",
    }
    sets = []
    values = []
    for k, v in kwargs.items():
        if k in allowed:
            sets.append(f"{k} = ?")
            values.append(v)
    if not sets:
        return
    values.append(user_id)
    await conn.execute(
        f"UPDATE users SET {', '.join(sets)} WHERE user_id = ?",
        tuple(values),
    )
    await conn.commit()


async def update_balance(
    user_id: int,
    real_balance: Optional[int] = None,
    demo_balance: Optional[int] = None,
    demo_mode: Optional[int] = None,
) -> None:
    """Update user_balances: only provided fields are updated."""
    conn = await get_connection()
    sets = []
    values = []
    if real_balance is not None:
        sets.append("real_balance = ?")
        values.append(real_balance)
    if demo_balance is not None:
        sets.append("demo_balance = ?")
        values.append(demo_balance)
    if demo_mode is not None:
        sets.append("demo_mode = ?")
        values.append(demo_mode)
    if not sets:
        return
    values.append(user_id)
    await conn.execute(
        f"UPDATE user_balances SET {', '.join(sets)} WHERE user_id = ?",
        tuple(values),
    )
    await conn.commit()


async def set_block(user_id: int, is_blocked: bool, block_type: Optional[str] = None) -> None:
    """Set is_blocked and block_type (full/partial)."""
    conn = await get_connection()
    await conn.execute(
        "UPDATE users SET is_blocked = ?, block_type = ? WHERE user_id = ?",
        (1 if is_blocked else 0, block_type, user_id),
    )
    await conn.commit()


def user_has_contact_sent(user: Optional[User]) -> bool:
    """
    True if user has sent contact: has_contact_sent == 1 or contact_phone is set.
    Handles NULL/None in DB for both fields; no comparison to 0 for contact_phone.
    """
    if user is None:
        return False
    if getattr(user, "has_contact_sent", None) == 1:
        return True
    phone = getattr(user, "contact_phone", None)
    if phone is None:
        return False
    return str(phone).strip() != ""


async def can_create_payment_request(user_id: int) -> bool:
    """
    Direct DB check: True only if user has sent contact.
    has_contact_sent = 1 OR (contact_phone IS NOT NULL AND TRIM(contact_phone) != '').
    Use this before creating any deposit/withdraw request.
    """
    conn = await get_connection()
    cursor = await conn.execute(
        "SELECT has_contact_sent, contact_phone FROM users WHERE user_id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    if not row:
        return False
    has_contact_sent = row[0]  # can be None if column was added later
    contact_phone = row[1]  # can be None
    if has_contact_sent == 1:
        return True
    if contact_phone is None:
        return False
    return str(contact_phone).strip() != ""


async def set_user_contact(user_id: int, phone: Optional[str]) -> None:
    """Set has_contact_sent=1 and contact_phone (after user shared contact)."""
    conn = await get_connection()
    await conn.execute(
        "UPDATE users SET has_contact_sent = 1, contact_phone = ? WHERE user_id = ?",
        (phone or "", user_id),
    )
    await conn.commit()


async def get_language(user_id: int) -> str:
    """Return user language code."""
    user = await get_user(user_id)
    return user.language if user else "en"


async def set_fast_mode(user_id: int, enabled: bool) -> None:
    """Set fast_mode (0/1)."""
    conn = await get_connection()
    await conn.execute(
        "UPDATE users SET fast_mode = ? WHERE user_id = ?",
        (1 if enabled else 0, user_id),
    )
    await conn.commit()


async def set_notifications(user_id: int, enabled: bool) -> None:
    """Set notifications_enabled (0/1)."""
    conn = await get_connection()
    await conn.execute(
        "UPDATE users SET notifications_enabled = ? WHERE user_id = ?",
        (1 if enabled else 0, user_id),
    )
    await conn.commit()


async def get_users_count() -> int:
    """Return total number of users (for admin stats)."""
    conn = await get_connection()
    cursor = await conn.execute("SELECT COUNT(*) FROM users")
    row = await cursor.fetchone()
    await cursor.close()
    return int(row[0]) if row else 0


async def find_users_by_query(query: str, limit: int = 20) -> List[User]:
    """Search users: if query is numeric return that user_id if exists; else search username LIKE %query%."""
    conn = await get_connection()
    if query.strip().isdigit():
        user_id = int(query.strip())
        user = await get_user(user_id)
        return [user] if user else []
    cursor = await conn.execute(
        "SELECT user_id, username, first_name, last_name, full_name, referral_link, "
        "created_at, is_blocked, block_type, language, notifications_enabled, fast_mode "
        "FROM users WHERE username LIKE ? LIMIT ?",
        (f"%{query.strip()}%", limit),
    )
    rows = await cursor.fetchall()
    await cursor.close()
    return [
        User(
            user_id=r[0],
            username=r[1],
            first_name=r[2] or "",
            last_name=r[3],
            full_name=r[4] or "",
            referral_link=r[5],
            created_at=r[6],
            is_blocked=r[7],
            block_type=r[8],
            language=r[9] or "en",
            notifications_enabled=r[10],
            fast_mode=r[11],
        )
        for r in rows
    ]


async def get_user_ids_with_notifications() -> List[int]:
    """Return user_id list for users with notifications_enabled=1 (for broadcast)."""
    conn = await get_connection()
    cursor = await conn.execute("SELECT user_id FROM users WHERE notifications_enabled = 1")
    rows = await cursor.fetchall()
    await cursor.close()
    return [r[0] for r in rows]

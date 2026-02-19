"""Payment_requests queries."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from bot.database.connection import get_connection
from bot.database.models import PaymentRequest


async def create_payment_request(
    user_id: int,
    request_type: str,
    amount: int,
    payment_method: Optional[str] = None,
    payment_details: Optional[str] = None,
) -> int:
    """Insert pending request. Returns new id."""
    conn = await get_connection()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cursor = await conn.execute(
        """
        INSERT INTO payment_requests (user_id, request_type, amount, status, payment_method, payment_details, created_at)
        VALUES (?, ?, ?, 'pending', ?, ?, ?)
        """,
        (user_id, request_type, amount, payment_method, payment_details, now),
    )
    await conn.commit()
    return cursor.lastrowid or 0


async def get_pending_requests(request_type: Optional[str] = None) -> List[PaymentRequest]:
    """Return pending requests, optionally filtered by type (deposit/withdraw)."""
    conn = await get_connection()
    if request_type:
        cursor = await conn.execute(
            "SELECT id, user_id, request_type, amount, status, payment_method, payment_details, created_at, processed_at, processed_by "
            "FROM payment_requests WHERE status = 'pending' AND request_type = ? ORDER BY created_at DESC",
            (request_type,),
        )
    else:
        cursor = await conn.execute(
            "SELECT id, user_id, request_type, amount, status, payment_method, payment_details, created_at, processed_at, processed_by "
            "FROM payment_requests WHERE status = 'pending' ORDER BY created_at DESC",
        )
    rows = await cursor.fetchall()
    await cursor.close()
    return [_row_to_payment(r) for r in rows]


async def get_requests_by_user(user_id: int) -> List[PaymentRequest]:
    """Return all requests for user."""
    conn = await get_connection()
    cursor = await conn.execute(
        "SELECT id, user_id, request_type, amount, status, payment_method, payment_details, created_at, processed_at, processed_by " "FROM payment_requests WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    )
    rows = await cursor.fetchall()
    await cursor.close()
    return [_row_to_payment(r) for r in rows]


async def get_payment_request(request_id: int) -> Optional[PaymentRequest]:
    """Return one request by id."""
    conn = await get_connection()
    cursor = await conn.execute(
        "SELECT id, user_id, request_type, amount, status, payment_method, payment_details, created_at, processed_at, processed_by " "FROM payment_requests WHERE id = ?",
        (request_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    return _row_to_payment(row) if row else None


async def set_payment_status(
    request_id: int,
    status: str,
    processed_at: Optional[str] = None,
    processed_by: Optional[int] = None,
) -> None:
    """Update status, processed_at, processed_by."""
    conn = await get_connection()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    at = processed_at or now
    await conn.execute(
        "UPDATE payment_requests SET status = ?, processed_at = ?, processed_by = ? WHERE id = ?",
        (status, at, processed_by, request_id),
    )
    await conn.commit()


def _row_to_payment(r: tuple) -> PaymentRequest:
    return PaymentRequest(
        id=r[0],
        user_id=r[1],
        request_type=r[2],
        amount=r[3],
        status=r[4],
        payment_method=r[5],
        payment_details=r[6],
        created_at=r[7],
        processed_at=r[8],
        processed_by=r[9],
    )

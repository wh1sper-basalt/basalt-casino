"""Currency conversion utilities."""

from typing import Optional

import aiohttp

_usd_rate_cache: Optional[float] = None
_last_fetch: float = 0
CACHE_TTL = 300


async def get_usd_rate() -> float:
    """Get USD/RUB exchange rate from CBR or fallback to 90."""
    global _usd_rate_cache, _last_fetch

    import time

    now = time.time()

    if _usd_rate_cache is not None and (now - _last_fetch) < CACHE_TTL:
        return _usd_rate_cache

    try:
        async with aiohttp.ClientSession() as session:
            url = "https://www.cbr-xml-daily.ru/latest.js"
            async with session.get(url, timeout=3) as response:
                if response.status == 200:
                    data = await response.json()
                    rate = data.get("rates", {}).get("USD")
                    if rate:
                        _usd_rate_cache = rate
                        _last_fetch = now
                        return rate
    except Exception:
        pass

    _usd_rate_cache = 90.0
    _last_fetch = now
    return 90.0


def format_currency_rub(amount: int) -> str:
    """Format amount in RUB."""
    return f"{amount:,} ₽".replace(",", " ")


def format_currency_usd(amount: int, rate: float) -> str:
    """Format amount in USD."""
    usd = round(amount / rate, 2)
    return f"{usd:.2f} $"

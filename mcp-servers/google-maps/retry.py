"""
Retry and caching utilities for resilient scraping.
"""

import asyncio
import hashlib
import json
import logging
import time
from pathlib import Path
from functools import wraps

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / ".cache"


async def retry_async(
    coro_fn,
    max_retries: int = 2,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """Retry an async function with exponential backoff.

    Args:
        coro_fn: Async callable (no args — use lambda or partial)
        max_retries: Maximum retry attempts
        backoff: Base delay multiplier (doubles each retry)
        exceptions: Exception types to catch

    Returns:
        Result of the coroutine, or None if all retries fail
    """
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return await coro_fn()
        except exceptions as e:
            last_error = e
            if attempt < max_retries:
                delay = backoff * (2 ** attempt)
                logger.debug(f"Retry {attempt + 1}/{max_retries} after {delay}s: {e}")
                await asyncio.sleep(delay)

    logger.warning(f"All {max_retries + 1} attempts failed: {last_error}")
    return None


class ResultCache:
    """Simple file-based cache for scraping results.

    Caches enrichment results to avoid re-scraping the same websites.
    TTL-based expiry (default 24 hours).
    """

    def __init__(self, ttl_seconds: int = 86400):
        self._ttl = ttl_seconds
        CACHE_DIR.mkdir(exist_ok=True)

    def _key(self, identifier: str) -> str:
        return hashlib.md5(identifier.encode()).hexdigest()

    def get(self, identifier: str) -> dict | None:
        """Get cached result, or None if expired/missing."""
        cache_file = CACHE_DIR / f"{self._key(identifier)}.json"
        if not cache_file.exists():
            return None

        try:
            data = json.loads(cache_file.read_text())
            if time.time() - data.get("_cached_at", 0) > self._ttl:
                cache_file.unlink(missing_ok=True)
                return None
            return data.get("result")
        except Exception:
            return None

    def set(self, identifier: str, result: dict):
        """Cache a result."""
        cache_file = CACHE_DIR / f"{self._key(identifier)}.json"
        try:
            cache_file.write_text(json.dumps({
                "_cached_at": time.time(),
                "result": result,
            }))
        except Exception:
            pass

    def clear(self):
        """Clear all cached results."""
        for f in CACHE_DIR.glob("*.json"):
            f.unlink(missing_ok=True)

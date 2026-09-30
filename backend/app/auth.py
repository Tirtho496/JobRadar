import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request

from app.config import get_settings

settings = get_settings()
_requests: dict[str, deque[float]] = defaultdict(deque)


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


async def rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    bucket = _requests[client]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= 120:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    bucket.append(now)

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RawJob:
    source: str
    source_job_id: str
    url: str
    title: str
    company: str
    location: str
    description: str
    date_posted: datetime | None = None
    deadline: datetime | None = None
    remote: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


def parse_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        timestamp = value / 1000 if value > 10_000_000_000 else value
        return datetime.fromtimestamp(timestamp, tz=UTC)
    try:
        parsed = date_parser.parse(str(value))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except (ValueError, TypeError, OverflowError):
        return None


class BaseCollector(ABC):
    name: str

    def __init__(self, timeout: float = 20.0) -> None:
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
            headers={"User-Agent": "JobRadar/1.0 (+local personal job discovery)"},
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def get_json(
        self, url: str, *, params: dict | None = None, headers: dict | None = None, retries: int = 3
    ) -> Any:
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                response = await self.client.get(url, params=params, headers=headers)
                if response.status_code == 429:
                    retry_after = min(float(response.headers.get("Retry-After", "2")), 15.0)
                    await asyncio.sleep(retry_after)
                    continue
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt < retries - 1:
                    await asyncio.sleep(min(2**attempt, 8))
        raise RuntimeError(f"{self.name} request failed: {last_error}") from last_error

    @abstractmethod
    async def collect(self) -> list[RawJob]:
        raise NotImplementedError

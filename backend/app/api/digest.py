from collections import defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import rate_limit, require_api_key
from app.db import get_session
from app.models import Job
from app.schemas import JobOut

router = APIRouter(prefix="/api/digest", tags=["digest"], dependencies=[Depends(require_api_key), Depends(rate_limit)])


@router.get("")
async def digest(
    hours: int = Query(default=24, ge=1, le=168),
    per_country: int = Query(default=25, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> dict:
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    stmt = (
        select(Job)
        .where(
            Job.is_active.is_(True),
            Job.eligible.is_(True),
            or_(Job.date_posted >= cutoff, and_(Job.date_posted.is_(None), Job.first_seen_at >= cutoff)),
        )
        .order_by(desc(Job.application_value == "HIGH"), desc(Job.fit_score), desc(Job.first_seen_at))
        .limit(500)
    )
    jobs = list((await session.scalars(stmt)).all())
    grouped: dict[str, list[dict]] = defaultdict(list)
    for job in jobs:
        bucket = grouped[job.country]
        if len(bucket) < per_country:
            bucket.append(JobOut.model_validate(job).model_dump(mode="json"))
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "hours": hours,
        "total": len(jobs),
        "countries": dict(grouped),
    }

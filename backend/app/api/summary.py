from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import rate_limit, require_api_key
from app.cache import cache
from app.db import get_session
from app.models import Job

router = APIRouter(prefix="/api/summary", tags=["summary"], dependencies=[Depends(require_api_key), Depends(rate_limit)])


@router.get("")
async def summary(session: AsyncSession = Depends(get_session)) -> dict:
    if cached := cache.get("summary"):
        return cached
    today = datetime.now(UTC) - timedelta(hours=24)
    base = (Job.is_active.is_(True), Job.eligible.is_(True))
    total = await session.scalar(select(func.count(Job.id)).where(*base)) or 0
    fresh = or_(Job.date_posted >= today, and_(Job.date_posted.is_(None), Job.first_seen_at >= today))
    new_today = await session.scalar(select(func.count(Job.id)).where(*base, fresh)) or 0
    high = await session.scalar(select(func.count(Job.id)).where(*base, Job.application_value == "HIGH")) or 0
    applied = await session.scalar(select(func.count(Job.id)).where(Job.status.in_(("APPLIED", "INTERVIEW", "REJECTED", "OFFER")))) or 0
    country_rows = (await session.execute(
        select(Job.country, func.count(Job.id)).where(*base).group_by(Job.country).order_by(Job.country)
    )).all()
    role_rows = (await session.execute(
        select(Job.role_family, func.count(Job.id)).where(*base).group_by(Job.role_family).order_by(func.count(Job.id).desc()).limit(8)
    )).all()
    result = {
        "total": total,
        "new_today": new_today,
        "high_value": high,
        "applied": applied,
        "countries": {country: count for country, count in country_rows},
        "roles": {role: count for role, count in role_rows},
    }
    cache.set("summary", result, ttl=45)
    return result

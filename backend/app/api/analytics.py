from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.auth import rate_limit, require_api_key
from app.cache import cache
from app.core.profile import get_profile
from app.db import SessionDep
from app.models import Job

router = APIRouter(
    prefix="/api/analytics", tags=["analytics"], dependencies=[Depends(require_api_key), Depends(rate_limit)]
)


@router.get("/skills")
async def skills(session: SessionDep) -> dict:
    if cached := cache.get("skills"):
        return cached
    rows = (await session.scalars(select(Job).where(Job.is_active.is_(True), Job.eligible.is_(True)))).all()
    demand = Counter(skill for job in rows for skill in (job.skills or []))
    profile_skills = set(get_profile().skills)
    items = [
        {"skill": skill, "jobs": count, "owned": skill in profile_skills} for skill, count in demand.most_common(40)
    ]
    gaps = [item for item in items if not item["owned"]][:12]
    result = {"total_jobs": len(rows), "skills": items, "top_gaps": gaps}
    cache.set("skills", result, ttl=120)
    return result

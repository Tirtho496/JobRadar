from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import rate_limit, require_api_key
from app.cache import cache
from app.db import get_session
from app.models import Feedback, Job
from app.schemas import FeedbackIn, JobDetail, JobOut, StatusUpdate

router = APIRouter(prefix="/api/jobs", tags=["jobs"], dependencies=[Depends(require_api_key), Depends(rate_limit)])


@router.get("", response_model=list[JobOut])
async def list_jobs(
    country: str | None = None,
    role_family: str | None = None,
    status: str | None = None,
    min_score: float = Query(default=50, ge=0, le=100),
    application_value: str | None = None,
    new_since_hours: int | None = Query(default=None, ge=1, le=720),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[Job]:
    stmt = select(Job).where(Job.is_active.is_(True), Job.eligible.is_(True), Job.fit_score >= min_score)
    if country:
        stmt = stmt.where(Job.country == country)
    if role_family:
        stmt = stmt.where(Job.role_family == role_family)
    if status:
        stmt = stmt.where(Job.status == status)
    if application_value:
        stmt = stmt.where(Job.application_value == application_value)
    if new_since_hours:
        cutoff = datetime.now(UTC) - timedelta(hours=new_since_hours)
        stmt = stmt.where(or_(Job.date_posted >= cutoff, and_(Job.date_posted.is_(None), Job.first_seen_at >= cutoff)))
    stmt = stmt.order_by(desc(Job.application_value == "HIGH"), desc(Job.fit_score), desc(Job.first_seen_at)).offset(offset).limit(limit)
    return list((await session.scalars(stmt)).all())


@router.get("/tracker", response_model=list[JobOut])
async def application_tracker(
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[Job]:
    tracked = ("SAVED", "APPLYING", "APPLIED", "INTERVIEW", "REJECTED", "OFFER")
    stmt = select(Job).where(Job.status.in_(tracked))
    if status:
        if status not in tracked:
            raise HTTPException(status_code=400, detail="Unsupported tracker status")
        stmt = stmt.where(Job.status == status)
    stmt = stmt.order_by(desc(Job.updated_at), desc(Job.fit_score)).limit(500)
    return list((await session.scalars(stmt)).all())


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: int, session: AsyncSession = Depends(get_session)) -> Job:
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/{job_id}/status", response_model=JobOut)
async def update_status(job_id: int, payload: StatusUpdate, session: AsyncSession = Depends(get_session)) -> Job:
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = payload.status
    await session.commit()
    await session.refresh(job)
    cache.clear()
    return job


@router.post("/{job_id}/feedback")
async def add_feedback(job_id: int, payload: FeedbackIn, session: AsyncSession = Depends(get_session)) -> dict:
    if not await session.get(Job, job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    feedback = Feedback(job_id=job_id, useful=payload.useful, reason=payload.reason)
    session.add(feedback)
    await session.commit()
    return {"status": "saved"}

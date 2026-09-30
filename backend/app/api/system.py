from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import rate_limit, require_api_key
from app.db import get_session
from app.models import SourceRun
from app.services.ingestion import ingestion_running

router = APIRouter(prefix="/api/system", tags=["system"], dependencies=[Depends(require_api_key), Depends(rate_limit)])


@router.get("/sources")
async def source_health(session: AsyncSession = Depends(get_session)) -> dict:
    runs = list((await session.scalars(select(SourceRun).order_by(desc(SourceRun.started_at)).limit(100))).all())
    latest: dict[str, SourceRun] = {}
    for run in runs:
        latest.setdefault(run.source, run)
    return {
        "ingestion_running": ingestion_running(),
        "sources": [
            {
                "source": run.source,
                "status": run.status,
                "started_at": run.started_at,
                "finished_at": run.finished_at,
                "fetched": run.fetched,
                "inserted": run.inserted,
                "eligible": run.eligible,
                "rejected": run.rejected,
                "duplicates": run.duplicates,
                "latency_ms": run.latency_ms,
                "error": run.error,
            }
            for run in latest.values()
        ],
    }

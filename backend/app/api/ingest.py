import asyncio

from fastapi import APIRouter, Depends

from app.auth import require_api_key
from app.schemas import IngestResponse
from app.services.ingestion import ingestion_running, run_ingestion

router = APIRouter(prefix="/api/ingest", tags=["ingestion"], dependencies=[Depends(require_api_key)])


@router.post("/run", response_model=IngestResponse, status_code=202)
async def start_ingestion() -> IngestResponse:
    if ingestion_running():
        return IngestResponse(status="running", message="A scan is already running")
    asyncio.create_task(run_ingestion())
    return IngestResponse(status="started", message="Job scan started")

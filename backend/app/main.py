import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text

from app.api import analytics, digest, ingest, jobs, model_lab, settings as settings_api, summary, system
from app.config import get_settings
from app.db import SessionLocal
from app.logging_config import configure_logging
from app.metrics import metrics
from app.services.ingestion import run_ingestion
from app.services.scheduler import start_scheduler, stop_scheduler

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    start_scheduler()
    if settings.scan_on_startup:
        asyncio.create_task(run_ingestion())
    yield
    stop_scheduler()


app = FastAPI(title="JobRadar API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_metrics(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
        metrics.inc("http_requests_total")
        if response.status_code >= 500:
            metrics.inc("http_5xx_total")
        return response
    finally:
        logger.info("request", extra={"path": request.url.path, "latency_ms": round((time.perf_counter() - started) * 1000, 2)})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "jobradar"}


@app.get("/ready")
async def ready() -> dict:
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "not_ready", "detail": str(exc)})


@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics() -> str:
    return metrics.render()


app.include_router(jobs.router)
app.include_router(summary.router)
app.include_router(digest.router)
app.include_router(analytics.router)
app.include_router(system.router)
app.include_router(ingest.router)
app.include_router(model_lab.router)
app.include_router(settings_api.router)

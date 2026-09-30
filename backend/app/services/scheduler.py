import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.services.ingestion import run_ingestion

logger = logging.getLogger(__name__)
settings = get_settings()
scheduler = AsyncIOScheduler(timezone=settings.app_timezone)


async def scheduled_ingestion() -> None:
    logger.info("scheduled ingestion started")
    await run_ingestion()


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        scheduled_ingestion,
        CronTrigger(
            hour=settings.daily_ingest_hour, minute=settings.daily_ingest_minute, timezone=settings.app_timezone
        ),
        id="daily_ingestion",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("scheduler started")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)

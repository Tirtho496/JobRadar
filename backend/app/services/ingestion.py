import asyncio
import hashlib
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import numpy as np
from sqlalchemy import select

from app.cache import cache
from app.collectors.base import BaseCollector, RawJob
from app.collectors.registry import build_collectors
from app.config import get_settings
from app.core.classifiers import (
    classify_language,
    classify_role,
    detect_seniority,
    extract_experience,
    extract_skills,
)
from app.core.dedupe import content_hash
from app.core.embedding import get_embedding_service
from app.core.profile import get_locations, get_profile
from app.core.scoring import score_job
from app.core.text import normalize_text
from app.db import SessionLocal
from app.metrics import metrics
from app.models import Feedback, Job, SourceRun

logger = logging.getLogger(__name__)
settings = get_settings()
_ingest_lock = asyncio.Lock()

SOURCE_PRIORITY = {
    "greenhouse": 5,
    "lever": 5,
    "smartrecruiters": 5,
    "platsbanken": 4,
    "jobbnorge": 4,
    "jobopportunities": 3,
    "arbeitnow": 2,
    "jobicy": 2,
    "remotive": 2,
    "remoteok": 1,
}


@dataclass(slots=True)
class PreparedJob:
    raw: RawJob
    country: str
    city: str | None
    language_status: str
    seniority: str
    role_family: str
    experience: object
    skills: list[str]
    job_text: str


def infer_geography(raw: RawJob) -> tuple[str | None, str | None]:
    locations = get_locations()
    location_text = f" {normalize_text(raw.location)} "
    fallback_text = location_text if raw.location.strip() else f" {normalize_text(raw.description[:500])} "
    for country, cfg in locations.countries.items():
        city_match = next((city for city in cfg.cities if normalize_text(city) in location_text), None)
        aliases = [normalize_text(country), normalize_text(cfg.code), *(normalize_text(alias) for alias in cfg.aliases)]
        if city_match or any(f" {alias} " in location_text for alias in aliases if alias):
            return country, city_match
    if not raw.location.strip():
        for country, cfg in locations.countries.items():
            city_match = next((city for city in cfg.cities if normalize_text(city) in fallback_text), None)
            aliases = [
                normalize_text(country),
                normalize_text(cfg.code),
                *(normalize_text(alias) for alias in cfg.aliases),
            ]
            if city_match or any(f" {alias} " in fallback_text for alias in aliases if alias):
                return country, city_match
    if raw.remote:
        haystack = f" {normalize_text(f'{raw.location} {raw.description[:700]}')} "
        worldwide = any(token in haystack for token in ("worldwide", "anywhere", "global remote"))
        excluded_only = any(
            token in haystack
            for token in (
                "united states only",
                "us only",
                "usa only",
                "north america only",
                "canada only",
                "latin america only",
                "australia only",
                "india only",
                "apac only",
            )
        )
        europe_signal = any(token in haystack for token in ("europe", "european", "emea", "eu remote", "europe only"))
        disallowed_region = any(
            token in haystack for token in ("united states", " usa ", "canada", "australia", "india")
        )
        if worldwide or europe_signal or ("remote" in haystack and not excluded_only and not disallowed_region):
            return "EU Remote", None
    return None, None


def _source_root(source: str) -> str:
    return source.split(":", 1)[0]


def _is_better_source(new_source: str, old_source: str) -> bool:
    return SOURCE_PRIORITY.get(_source_root(new_source), 0) > SOURCE_PRIORITY.get(_source_root(old_source), 0)


def prepare_job(raw: RawJob) -> PreparedJob | None:
    country, city = infer_geography(raw)
    if not country:
        return None
    locations = get_locations()
    language = classify_language(raw.description, country if country != "EU Remote" else "", locations)
    seniority = detect_seniority(raw.title, raw.description)
    experience = extract_experience(f"{raw.title} {raw.description}")
    role_family = classify_role(raw.title, raw.description)
    skills = extract_skills(f"{raw.title} {raw.description}")
    return PreparedJob(
        raw=raw,
        country=country,
        city=city,
        language_status=language.status,
        seniority=seniority,
        role_family=role_family,
        experience=experience,
        skills=skills,
        job_text=f"{raw.title}\n{raw.description[:8000]}",
    )


@dataclass(slots=True)
class FeedbackPreferences:
    role: dict[str, float]
    skill: dict[str, float]
    samples: int


async def _load_feedback_preferences() -> FeedbackPreferences:
    async with SessionLocal() as session:
        rows = (
            await session.execute(
                select(Feedback.useful, Job.role_family, Job.skills)
                .join(Job, Feedback.job_id == Job.id)
                .order_by(Feedback.created_at.desc())
                .limit(250)
            )
        ).all()
    if len(rows) < 3:
        return FeedbackPreferences({}, {}, len(rows))
    role_sum: dict[str, float] = defaultdict(float)
    role_count: dict[str, int] = defaultdict(int)
    skill_sum: dict[str, float] = defaultdict(float)
    skill_count: dict[str, int] = defaultdict(int)
    for useful, role_family, skills in rows:
        value = 1.0 if useful else -1.0
        if role_family:
            role_sum[role_family] += value
            role_count[role_family] += 1
        for skill in skills or []:
            skill_sum[skill] += value
            skill_count[skill] += 1
    role = {key: role_sum[key] / role_count[key] for key in role_sum}
    skill = {key: skill_sum[key] / skill_count[key] for key in skill_sum}
    return FeedbackPreferences(role, skill, len(rows))


def _preference_boost(item: PreparedJob, preferences: FeedbackPreferences) -> float:
    if preferences.samples < 3:
        return 0.0
    role_signal = preferences.role.get(item.role_family, 0.0)
    skill_signals = [preferences.skill[skill] for skill in item.skills if skill in preferences.skill]
    skill_signal = sum(skill_signals) / len(skill_signals) if skill_signals else 0.0
    return round(max(-5.0, min(5.0, 3.0 * role_signal + 2.0 * skill_signal)), 3)


def _embedding_candidate(item: PreparedJob) -> bool:
    profile = get_profile()
    if item.seniority == "SENIOR" and profile.constraints.reject_senior_titles:
        return False
    if item.language_status == "LOCAL_REQUIRED":
        return False
    if item.language_status == "LOCAL_OPTIONAL" and not profile.constraints.allow_local_language_optional:
        return False
    if (
        item.language_status == "UNCLEAR"
        and profile.constraints.require_english_compatible
        and not settings.allow_unclear_language
    ):
        return False
    if item.experience.minimum is not None:
        max_req = item.experience.maximum if item.experience.maximum is not None else item.experience.minimum
        if item.experience.minimum > profile.constraints.borderline_required_years:
            return False
        if (
            item.experience.minimum >= profile.constraints.max_required_years
            and max_req > profile.constraints.borderline_required_years
        ):
            return False
    return True


async def _process_source(
    collector: BaseCollector, semaphore: asyncio.Semaphore, preferences: FeedbackPreferences
) -> dict:
    async with semaphore:
        started = time.perf_counter()
        async with SessionLocal() as session:
            run = SourceRun(source=collector.name, status="RUNNING")
            session.add(run)
            await session.commit()
            await session.refresh(run)
            try:
                raw_jobs = await collector.collect()
                run.fetched = len(raw_jobs)
                prepared = [item for raw in raw_jobs if (item := prepare_job(raw)) is not None]

                embedding_service = get_embedding_service()
                profile = get_profile()
                profile_text = f"{profile.headline}. {profile.summary}. Roles: {'; '.join(profile.preferred_roles)}. Skills: {'; '.join(profile.skills)}"
                embedding_items = [(index, item) for index, item in enumerate(prepared) if _embedding_candidate(item)]
                vector_by_index: dict[int, list[float]] = {}
                profile_vector = None
                if embedding_items and settings.embedding_enabled:
                    texts = [profile_text] + [item.job_text[:5000] for _, item in embedding_items]
                    vectors = await asyncio.to_thread(embedding_service.encode, texts)
                    if vectors:
                        profile_vector = np.asarray(vectors[0])
                        vector_by_index = {
                            original_index: vector
                            for (original_index, _), vector in zip(embedding_items, vectors[1:], strict=True)
                        }

                for index, item in enumerate(prepared):
                    semantic_score = 0.0 if not _embedding_candidate(item) else None
                    embedding_vector = vector_by_index.get(index)
                    if embedding_vector is not None and profile_vector is not None:
                        semantic_score = float(np.dot(profile_vector, np.asarray(embedding_vector)))
                    result = score_job(
                        title=item.raw.title,
                        description=item.raw.description,
                        location=item.raw.location,
                        country=item.country,
                        seniority=item.seniority,
                        language_status=item.language_status,
                        experience=item.experience,
                        date_posted=item.raw.date_posted,
                        profile=profile,
                        embedding_service=embedding_service,
                        semantic_score=semantic_score,
                        embedding_vector=embedding_vector,
                        allow_unclear_language=settings.allow_unclear_language,
                        preference_boost_points=_preference_boost(item, preferences),
                    )
                    job_hash = content_hash(item.raw.company, item.raw.title, item.raw.location)
                    external_id = item.raw.source_job_id
                    if len(external_id) > 240:
                        external_id = hashlib.sha256(external_id.encode("utf-8")).hexdigest()
                    existing = await session.scalar(
                        select(Job).where(Job.source == item.raw.source, Job.source_job_id == external_id)
                    )
                    duplicate = None
                    if not existing:
                        duplicate = await session.scalar(
                            select(Job).where(Job.content_hash == job_hash).order_by(Job.id.asc())
                        )
                    if duplicate and duplicate.source != item.raw.source:
                        sources = set(duplicate.duplicate_sources or [])
                        sources.add(item.raw.source)
                        duplicate.duplicate_sources = sorted(sources)
                        duplicate.last_seen_at = datetime.now(UTC)
                        if _is_better_source(item.raw.source, duplicate.source):
                            duplicate.source = item.raw.source
                            duplicate.source_job_id = external_id
                            duplicate.canonical_url = item.raw.url or duplicate.canonical_url
                        run.duplicates += 1
                        continue

                    job = existing or Job(source=item.raw.source, source_job_id=external_id)
                    job.canonical_url = item.raw.url
                    job.title = item.raw.title
                    job.company = item.raw.company
                    job.country = item.country
                    job.city = item.city
                    job.location = item.raw.location
                    job.remote = item.raw.remote
                    job.description = item.raw.description
                    job.date_posted = item.raw.date_posted
                    job.deadline = item.raw.deadline
                    job.language_status = item.language_status
                    job.experience_min = item.experience.minimum
                    job.experience_max = item.experience.maximum
                    job.seniority = item.seniority
                    job.role_family = item.role_family
                    job.skills = item.skills
                    job.matched_skills = result.matched_skills
                    job.missing_skills = result.missing_skills
                    job.fit_score = result.fit_score
                    job.eligibility = result.eligibility
                    job.application_value = result.application_value
                    job.score_breakdown = result.breakdown
                    job.reasons = result.reasons
                    job.rejection_reasons = result.rejection_reasons
                    job.eligible = result.eligible
                    job.content_hash = job_hash
                    job.embedding = result.embedding
                    job.is_active = True
                    job.last_seen_at = datetime.now(UTC)
                    if existing is None:
                        session.add(job)
                        run.inserted += 1
                    if result.eligible:
                        run.eligible += 1
                    else:
                        run.rejected += 1
                await session.commit()
                run.status = "SUCCESS"
                metrics.inc("source_success_total")
                metrics.inc("jobs_fetched_total", run.fetched)
                metrics.inc("jobs_inserted_total", run.inserted)
            except Exception as exc:
                await session.rollback()
                run = await session.get(SourceRun, run.id)
                if run:
                    run.status = "FAILED"
                    run.error = str(exc)[:2000]
                metrics.inc("source_failure_total")
                logger.exception("source ingestion failed", extra={"source": collector.name})
            finally:
                try:
                    await collector.close()
                except Exception:
                    logger.warning("collector close failed", extra={"source": collector.name})
                run = await session.get(SourceRun, run.id)
                if run:
                    run.finished_at = datetime.now(UTC)
                    run.latency_ms = round((time.perf_counter() - started) * 1000, 2)
                    await session.commit()
            return {
                "source": collector.name,
                "status": run.status if run else "FAILED",
                "fetched": run.fetched if run else 0,
                "inserted": run.inserted if run else 0,
                "eligible": run.eligible if run else 0,
                "rejected": run.rejected if run else 0,
                "duplicates": run.duplicates if run else 0,
            }


async def cleanup_stale_jobs() -> None:
    cutoff = datetime.now(UTC) - timedelta(days=45)
    async with SessionLocal() as session:
        jobs = (await session.scalars(select(Job).where(Job.is_active.is_(True)))).all()
        changed = False
        for job in jobs:
            deadline_expired = bool(job.deadline and job.deadline < datetime.now(UTC))
            stale = job.last_seen_at < cutoff
            if deadline_expired or stale:
                job.is_active = False
                changed = True
        if changed:
            await session.commit()


async def run_ingestion() -> list[dict]:
    if _ingest_lock.locked():
        return [{"source": "system", "status": "ALREADY_RUNNING"}]
    async with _ingest_lock:
        cache.clear()
        collectors = build_collectors()
        preferences = await _load_feedback_preferences()
        semaphore = asyncio.Semaphore(settings.max_concurrent_sources)
        results = await asyncio.gather(
            *(_process_source(collector, semaphore, preferences) for collector in collectors)
        )
        await cleanup_stale_jobs()
        return list(results)


def ingestion_running() -> bool:
    return _ingest_lock.locked()

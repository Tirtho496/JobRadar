from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    duplicate_sources: list
    canonical_url: str
    title: str
    company: str
    country: str
    city: str | None
    location: str
    remote: bool
    date_posted: datetime | None
    language_status: str
    experience_min: float | None
    experience_max: float | None
    seniority: str
    role_family: str
    skills: list
    matched_skills: list
    missing_skills: list
    fit_score: float
    eligibility: str
    application_value: str
    score_breakdown: dict
    reasons: list
    status: str
    first_seen_at: datetime


class JobDetail(JobOut):
    description: str
    rejection_reasons: list


class StatusUpdate(BaseModel):
    status: str = Field(pattern="^(NEW|SAVED|APPLYING|APPLIED|INTERVIEW|REJECTED|OFFER|IGNORED)$")


class FeedbackIn(BaseModel):
    useful: bool
    reason: str | None = None


class IngestResponse(BaseModel):
    status: str
    message: str

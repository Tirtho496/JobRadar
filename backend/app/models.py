from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source", "source_job_id", name="uq_job_source_external"),
        Index("ix_jobs_country_eligible", "country", "eligible"),
        Index("ix_jobs_fit_score", "fit_score"),
        Index("ix_jobs_first_seen", "first_seen_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(80), index=True)
    source_job_id: Mapped[str] = mapped_column(String(255))
    duplicate_sources: Mapped[list] = mapped_column(JSONB, default=list)
    canonical_url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    company: Mapped[str] = mapped_column(Text)
    country: Mapped[str] = mapped_column(String(80), index=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    location: Mapped[str] = mapped_column(Text, default="")
    remote: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(Text, default="")
    date_posted: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    language_status: Mapped[str] = mapped_column(String(60), index=True)
    experience_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    experience_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    seniority: Mapped[str] = mapped_column(String(40), index=True)
    role_family: Mapped[str] = mapped_column(String(80), index=True)
    skills: Mapped[list] = mapped_column(JSONB, default=list)
    matched_skills: Mapped[list] = mapped_column(JSONB, default=list)
    missing_skills: Mapped[list] = mapped_column(JSONB, default=list)
    fit_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    eligibility: Mapped[str] = mapped_column(String(30), index=True)
    application_value: Mapped[str] = mapped_column(String(30), index=True)
    score_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)
    reasons: Mapped[list] = mapped_column(JSONB, default=list)
    rejection_reasons: Mapped[list] = mapped_column(JSONB, default=list)
    eligible: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="NEW", index=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    feedback: Mapped[list["Feedback"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    useful: Mapped[bool] = mapped_column(Boolean)
    reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    job: Mapped[Job] = relationship(back_populates="feedback")


class SourceRun(Base):
    __tablename__ = "source_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(120), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    fetched: Mapped[int] = mapped_column(Integer, default=0)
    inserted: Mapped[int] = mapped_column(Integer, default=0)
    eligible: Mapped[int] = mapped_column(Integer, default=0)
    rejected: Mapped[int] = mapped_column(Integer, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)


class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(255), index=True)
    dataset_name: Mapped[str] = mapped_column(String(255))
    precision_at_10: Mapped[float | None] = mapped_column(Float, nullable=True)
    ndcg_at_10: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    mean_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

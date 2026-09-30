"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-25
"""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("source_job_id", sa.String(length=255), nullable=False),
        sa.Column("duplicate_sources", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("company", sa.Text(), nullable=False),
        sa.Column("country", sa.String(length=80), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("location", sa.Text(), nullable=False, server_default=""),
        sa.Column("remote", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("date_posted", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("language_status", sa.String(length=60), nullable=False),
        sa.Column("experience_min", sa.Float(), nullable=True),
        sa.Column("experience_max", sa.Float(), nullable=True),
        sa.Column("seniority", sa.String(length=40), nullable=False),
        sa.Column("role_family", sa.String(length=80), nullable=False),
        sa.Column("skills", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("matched_skills", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("missing_skills", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("fit_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("eligibility", sa.String(length=30), nullable=False),
        sa.Column("application_value", sa.String(length=30), nullable=False),
        sa.Column("score_breakdown", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("reasons", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("rejection_reasons", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("eligible", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="NEW"),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("source", "source_job_id", name="uq_job_source_external"),
    )
    for name, columns in [
        ("ix_jobs_source", ["source"]),
        ("ix_jobs_country_eligible", ["country", "eligible"]),
        ("ix_jobs_fit_score", ["fit_score"]),
        ("ix_jobs_first_seen", ["first_seen_at"]),
        ("ix_jobs_language_status", ["language_status"]),
        ("ix_jobs_seniority", ["seniority"]),
        ("ix_jobs_role_family", ["role_family"]),
        ("ix_jobs_eligibility", ["eligibility"]),
        ("ix_jobs_application_value", ["application_value"]),
        ("ix_jobs_eligible", ["eligible"]),
        ("ix_jobs_status", ["status"]),
        ("ix_jobs_content_hash", ["content_hash"]),
        ("ix_jobs_is_active", ["is_active"]),
    ]:
        op.create_index(name, "jobs", columns)

    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("useful", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_feedback_job_id", "feedback", ["job_id"])

    op.create_table(
        "source_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(length=120), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("eligible", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
    )
    op.create_index("ix_source_runs_source", "source_runs", ["source"])
    op.create_index("ix_source_runs_status", "source_runs", ["status"])

    op.create_table(
        "model_evaluations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("dataset_name", sa.String(length=255), nullable=False),
        sa.Column("precision_at_10", sa.Float(), nullable=True),
        sa.Column("ndcg_at_10", sa.Float(), nullable=True),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("mean_latency_ms", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_model_evaluations_model_name", "model_evaluations", ["model_name"])


def downgrade() -> None:
    op.drop_table("model_evaluations")
    op.drop_table("source_runs")
    op.drop_table("feedback")
    op.drop_table("jobs")
    op.execute("DROP EXTENSION IF EXISTS vector")

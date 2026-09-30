from app.core.classifiers import ExperienceRequirement
from app.core.profile import CandidateProfile, Constraints
from app.core.scoring import score_job


class FakeEmbedding:
    def similarity(self, a: str, b: str) -> float:
        return 0.8

    def encode(self, texts: list[str]):
        return None


PROFILE = CandidateProfile(
    name="Example Candidate",
    headline="Software Engineer",
    experience_level="configurable",
    commercial_experience_years=0,
    summary="Software engineer working with Python services and data systems.",
    preferred_roles=["software engineer", "data engineer"],
    skills=["Python", "SQL", "Docker", "Git"],
    domain_strengths=["software engineering", "data systems"],
    constraints=Constraints(max_required_years=2, borderline_required_years=3),
)


def test_matching_job_is_eligible():
    result = score_job(
        title="Software Engineer",
        description="Build Python services using SQL and Docker. English is our working language.",
        location="Berlin",
        country="Germany",
        seniority="UNSPECIFIED",
        language_status="ENGLISH_COMPATIBLE",
        experience=ExperienceRequirement(1, 2, True),
        date_posted=None,
        profile=PROFILE,
        embedding_service=FakeEmbedding(),
        semantic_score=0.8,
    )
    assert result.eligible
    assert result.fit_score >= 60


def test_senior_job_is_rejected_even_with_skill_overlap():
    result = score_job(
        title="Senior Software Engineer",
        description="Python SQL Docker Git",
        location="Berlin",
        country="Germany",
        seniority="SENIOR",
        language_status="ENGLISH_COMPATIBLE",
        experience=ExperienceRequirement(6, 6, True),
        date_posted=None,
        profile=PROFILE,
        embedding_service=FakeEmbedding(),
        semantic_score=0.95,
    )
    assert not result.eligible
    assert "Senior/leadership title" in result.rejection_reasons


def test_above_ceiling_role_is_rejected():
    result = score_job(
        title="Software Engineer",
        description="Python SQL Docker",
        location="Berlin",
        country="Germany",
        seniority="UNSPECIFIED",
        language_status="ENGLISH_COMPATIBLE",
        experience=ExperienceRequirement(4, 5, True),
        date_posted=None,
        profile=PROFILE,
        embedding_service=FakeEmbedding(),
        semantic_score=0.9,
    )
    assert not result.eligible
    assert result.eligibility == "LOW"


def test_borderline_role_is_not_hard_rejected():
    result = score_job(
        title="Software Engineer",
        description="Python SQL Docker Git",
        location="Berlin",
        country="Germany",
        seniority="UNSPECIFIED",
        language_status="ENGLISH_COMPATIBLE",
        experience=ExperienceRequirement(3, 3, True),
        date_posted=None,
        profile=PROFILE,
        embedding_service=FakeEmbedding(),
        semantic_score=0.9,
    )
    assert result.eligibility == "BORDERLINE"

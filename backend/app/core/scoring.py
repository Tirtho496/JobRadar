from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.classifiers import ExperienceRequirement, extract_skills, role_similarity
from app.core.embedding import EmbeddingService
from app.core.profile import CandidateProfile
from app.core.text import normalize_text

WEIGHTS = {
    "technical": 0.25,
    "experience": 0.20,
    "role": 0.20,
    "semantic": 0.15,
    "domain": 0.10,
    "education": 0.05,
    "location": 0.05,
}


@dataclass(slots=True)
class ScoreResult:
    fit_score: float
    eligibility: str
    application_value: str
    breakdown: dict[str, float]
    matched_skills: list[str]
    missing_skills: list[str]
    reasons: list[str]
    rejection_reasons: list[str]
    eligible: bool
    embedding: list[float] | None


def _experience_score(exp: ExperienceRequirement, profile: CandidateProfile) -> tuple[float, str, list[str]]:
    reasons: list[str] = []
    max_allowed = profile.constraints.max_required_years
    borderline = profile.constraints.borderline_required_years
    if not exp.explicit or exp.minimum is None:
        return 0.8, "HIGH", reasons

    minimum = exp.minimum
    maximum = exp.maximum if exp.maximum is not None else exp.minimum
    if minimum > borderline:
        reasons.append(f"Experience requirement is above the configured ceiling: {minimum:g}+ years")
        return 0.0, "LOW", reasons
    if minimum >= max_allowed and maximum > borderline:
        reasons.append(f"Experience range is too senior for the configured profile: {minimum:g}-{maximum:g} years")
        return 0.0, "LOW", reasons
    if minimum > max_allowed or maximum > max_allowed:
        reasons.append(f"Borderline experience requirement: {minimum:g}-{maximum:g} years")
        return 0.55, "BORDERLINE", reasons
    return 1.0, "HIGH", reasons


def score_job(
    *,
    title: str,
    description: str,
    location: str,
    country: str,
    seniority: str,
    language_status: str,
    experience: ExperienceRequirement,
    date_posted: datetime | None,
    profile: CandidateProfile,
    embedding_service: EmbeddingService,
    semantic_score: float | None = None,
    embedding_vector: list[float] | None = None,
    allow_unclear_language: bool = False,
    preference_boost_points: float = 0.0,
) -> ScoreResult:
    job_text = f"{title}\n{description}"
    job_skills = extract_skills(job_text)
    candidate_skills = set(profile.skills)
    matched = sorted(candidate_skills & set(job_skills))
    market_gaps = sorted(set(job_skills) - candidate_skills)
    technical = len(matched) / max(len(set(job_skills)), 1) if job_skills else 0.45
    role = role_similarity(title, profile)
    exp_score, exp_eligibility, exp_reasons = _experience_score(experience, profile)
    profile_text = f"{profile.headline}. {profile.summary}. Roles: {'; '.join(profile.preferred_roles)}. Skills: {'; '.join(profile.skills)}"
    semantic = (
        semantic_score if semantic_score is not None else embedding_service.similarity(profile_text, job_text[:5000])
    )
    semantic = max(0.0, min(1.0, semantic))
    normalized = normalize_text(job_text)
    domain_hits = [domain for domain in profile.domain_strengths if normalize_text(domain) in normalized]
    domain = min(1.0, 0.25 + 0.2 * len(domain_hits)) if domain_hits else 0.25
    education = (
        1.0
        if any(term in normalized for term in ("master", "msc", "computer science", "engineering degree", "bachelor"))
        else 0.8
    )
    location_score = 0.9 if country == "EU Remote" else 1.0 if country else 0.2

    breakdown = {
        "technical": technical,
        "experience": exp_score,
        "role": role,
        "semantic": semantic,
        "domain": domain,
        "education": education,
        "location": location_score,
    }
    weighted = sum(breakdown[key] * WEIGHTS[key] for key in WEIGHTS)
    rejection: list[str] = []
    if seniority == "SENIOR" and profile.constraints.reject_senior_titles:
        rejection.append("Senior/leadership title")
    if exp_eligibility == "LOW":
        rejection.extend(exp_reasons)
    if language_status == "LOCAL_REQUIRED":
        rejection.append("Mandatory local-language requirement")
    if language_status == "LOCAL_OPTIONAL" and not profile.constraints.allow_local_language_optional:
        rejection.append("Local-language preference is not allowed by the configured policy")
    if language_status == "UNCLEAR" and profile.constraints.require_english_compatible and not allow_unclear_language:
        rejection.append("Working language is unclear")
    if role < 0.2 and technical < 0.3:
        rejection.append("Low role and technical overlap")

    preference_boost_points = max(-5.0, min(5.0, preference_boost_points))
    fit_score = round(max(0.0, min(100.0, weighted * 100 + preference_boost_points)), 1)
    breakdown["feedback_boost_points"] = round(preference_boost_points, 4)
    eligible = not rejection and fit_score >= 50
    eligibility = exp_eligibility if eligible else "LOW"

    age_bonus = 0.0
    if date_posted:
        posted = date_posted if date_posted.tzinfo else date_posted.replace(tzinfo=UTC)
        age_days = max(0, (datetime.now(UTC) - posted).days)
        age_bonus = max(0.0, 10.0 - age_days * 1.5)
    application_numeric = fit_score + age_bonus
    if eligible and application_numeric >= 85 and language_status in {"ENGLISH_COMPATIBLE", "LOCAL_OPTIONAL"}:
        application_value = "HIGH"
    elif eligible and application_numeric >= 67:
        application_value = "MEDIUM"
    elif eligible:
        application_value = "LOW"
    else:
        application_value = "REJECT"

    reasons = []
    if matched:
        reasons.append("Strong skill overlap: " + ", ".join(matched[:6]))
    if domain_hits:
        reasons.append("Relevant domain overlap: " + ", ".join(domain_hits[:3]))
    if role >= 0.75:
        reasons.append("Role title closely matches configured target roles")
    if language_status == "LOCAL_OPTIONAL":
        reasons.append("Local language is optional rather than mandatory")
    if language_status == "ENGLISH_COMPATIBLE":
        reasons.append("English-compatible posting with no mandatory local-language requirement detected")
    reasons.extend(exp_reasons)
    if preference_boost_points >= 1.0:
        reasons.append("Similar roles/skills received positive recommendation feedback")
    elif preference_boost_points <= -1.0:
        reasons.append("Similar roles/skills received negative recommendation feedback")

    embedding = embedding_vector
    if embedding is None and semantic_score is None:
        vectors = embedding_service.encode([job_text[:5000]])
        if vectors:
            embedding = vectors[0]

    return ScoreResult(
        fit_score=fit_score,
        eligibility=eligibility,
        application_value=application_value,
        breakdown={key: round(value, 4) for key, value in breakdown.items()},
        matched_skills=matched,
        missing_skills=market_gaps[:12],
        reasons=reasons[:6],
        rejection_reasons=rejection,
        eligible=eligible,
        embedding=embedding,
    )

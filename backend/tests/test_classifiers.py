from app.core.classifiers import classify_language, detect_seniority, extract_experience, extract_skills
from app.core.profile import CountryConfig, LocationsConfig

LOCATIONS = LocationsConfig(countries={
    "Germany": CountryConfig(code="DE", cities=["Berlin"], local_languages=["German"], aliases=["Deutschland"]),
})


def test_rejects_mandatory_local_language():
    result = classify_language("Fluent German and English are required for this role.", "Germany", LOCATIONS)
    assert result.status == "LOCAL_REQUIRED"


def test_allows_optional_local_language():
    result = classify_language("Our working language is English. German is considered a plus.", "Germany", LOCATIONS)
    assert result.status == "LOCAL_OPTIONAL"


def test_english_posting_without_local_requirement():
    result = classify_language("You will join the engineering team and build Python services.", "Germany", LOCATIONS)
    assert result.status == "ENGLISH_COMPATIBLE"


def test_senior_title_detection():
    assert detect_seniority("Senior Software Engineer") == "SENIOR"
    assert detect_seniority("Graduate Software Engineer") == "JUNIOR"


def test_experience_range():
    result = extract_experience("We are looking for 1-3 years of professional experience.")
    assert result.minimum == 1
    assert result.maximum == 3


def test_skill_extraction():
    skills = extract_skills("Build APIs in Python and FastAPI, deploy with Docker and Kubernetes, track with MLflow.")
    assert {"Python", "FastAPI", "Docker", "Kubernetes", "MLflow"}.issubset(set(skills))


def test_optional_fluent_local_language_is_not_treated_as_mandatory():
    result = classify_language("English is our working language. Fluent German is an advantage, not required.", "Germany", LOCATIONS)
    assert result.status == "LOCAL_OPTIONAL"

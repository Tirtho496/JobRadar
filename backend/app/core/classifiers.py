import re
from dataclasses import dataclass

from app.core.profile import CandidateProfile, LocationsConfig
from app.core.text import normalize_text


SENIOR_TITLE_TERMS = {
    "senior", "sr", "staff", "principal", "lead", "manager", "director",
    "head", "chief", "vp", "vice president", "architect"
}
JUNIOR_TERMS = {"junior", "jr", "graduate", "entry level", "trainee", "intern", "early career"}

ROLE_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("ML Engineering", ("machine learning engineer", "ml engineer", "ml systems", "ai/ml engineer")),
    ("AI Engineering", ("ai engineer", "artificial intelligence engineer", "generative ai", "genai", "rag engineer")),
    ("Data Science", ("data scientist", "applied scientist", "decision scientist")),
    ("Research", ("research engineer", "research scientist", "ml researcher", "ai researcher")),
    ("Computer Vision", ("computer vision", "vision engineer", "image processing")),
    ("NLP", ("nlp engineer", "natural language processing", "language model")),
    ("MLOps", ("mlops", "machine learning platform", "ai platform engineer")),
    ("Data Engineering", ("data engineer", "analytics engineer")),
    ("Software Engineering", ("software engineer", "python engineer", "backend engineer", "developer")),
]

SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "PyTorch": ("pytorch", "torch"),
    "TensorFlow": ("tensorflow",),
    "Keras": ("keras",),
    "Hugging Face": ("hugging face", "huggingface", "transformers"),
    "OpenCV": ("opencv",),
    "scikit-learn": ("scikit-learn", "sklearn"),
    "RAG": ("retrieval augmented generation", "retrieval-augmented generation", " rag "),
    "Agentic RAG": ("agentic rag",),
    "LLM": ("large language model", "llm", "llms"),
    "LangChain": ("langchain",),
    "MCP": ("model context protocol", "mcp server", "mcp servers"),
    "Vision-Language Models": ("vision-language", "vision language", "vlm", "vlms"),
    "CLIP": ("clip",),
    "BERT": ("bert",),
    "MLflow": ("mlflow",),
    "Kubeflow": ("kubeflow",),
    "Docker": ("docker", "containerization", "containers"),
    "Kubernetes": ("kubernetes", "k8s"),
    "AWS": ("aws", "amazon web services", "sagemaker"),
    "Azure": ("azure",),
    "GCP": ("gcp", "google cloud"),
    "Git": ("git", "github", "gitlab"),
    "OpenSearch": ("opensearch",),
    "pgvector": ("pgvector",),
    "Milvus": ("milvus",),
    "Neo4j": ("neo4j",),
    "PostgreSQL": ("postgresql", "postgres"),
    "MySQL": ("mysql",),
    "MongoDB": ("mongodb",),
    "REST API": ("rest api", "restful", "fastapi", "api development"),
    "FastAPI": ("fastapi",),
    "Spark": ("apache spark", "pyspark", "spark"),
    "Databricks": ("databricks",),
    "Terraform": ("terraform", "infrastructure as code"),
    "CI/CD": ("ci/cd", "continuous integration", "continuous delivery", "github actions"),
    "Java": ("java",),
    "C++": ("c++", "cpp"),
    "SQL": (" sql ", "structured query language"),
    "Airflow": ("airflow", "apache airflow"),
    "Ray": (" ray ", "ray.io"),
    "ONNX": ("onnx",),
}


@dataclass(slots=True)
class ExperienceRequirement:
    minimum: float | None
    maximum: float | None
    explicit: bool


@dataclass(slots=True)
class LanguageResult:
    status: str
    note: str


def detect_seniority(title: str, description: str = "") -> str:
    text = normalize_text(title)
    words = set(text.replace("/", " ").split())
    if any(term in text for term in JUNIOR_TERMS):
        return "JUNIOR"
    if any(term in words or term in text for term in SENIOR_TITLE_TERMS):
        return "SENIOR"
    if re.search(r"\b(mid[- ]?level|intermediate)\b", text):
        return "MID"
    if "intern" in text or "trainee" in text:
        return "ENTRY"
    return "UNSPECIFIED"


def extract_experience(text: str) -> ExperienceRequirement:
    t = normalize_text(text)
    ranges = re.findall(r"\b(\d{1,2})\s*(?:-|–|to)\s*(\d{1,2})\s*(?:\+\s*)?(?:years?|yrs?)\b", t)
    singles = re.findall(r"\b(\d{1,2})\s*\+?\s*(?:years?|yrs?)\b", t)
    values: list[tuple[float, float]] = []
    for lo, hi in ranges:
        values.append((float(lo), float(hi)))
    for value in singles:
        number = float(value)
        if not any(str(int(number)) in pair for pair in ranges):
            values.append((number, number))
    if not values:
        if any(term in t for term in ("no experience required", "recent graduate", "new graduate", "entry level", "graduate programme", "graduate program")):
            return ExperienceRequirement(0.0, 1.0, True)
        return ExperienceRequirement(None, None, False)
    minimum = min(v[0] for v in values)
    maximum = max(v[1] for v in values)
    return ExperienceRequirement(minimum, maximum, True)


def classify_language(description: str, country: str, locations: LocationsConfig) -> LanguageResult:
    text = normalize_text(description)
    if not text:
        return LanguageResult("UNCLEAR", "No description available")
    country_cfg = locations.countries.get(country)
    local_languages = country_cfg.local_languages if country_cfg else []
    mandatory_hits: list[str] = []
    optional_hits: list[str] = []
    for language in local_languages:
        lang = normalize_text(language)
        optional_patterns = [
            rf"{lang}.{{0,45}}(?:plus|bonus|advantage|preferred|nice to have|merit|optional|not required)",
            rf"(?:plus|bonus|advantage|preferred|nice to have|merit|optional).{{0,45}}{lang}",
        ]
        required_patterns = [
            rf"(?:fluent|fluency|professional|excellent|strong|native|proficient|working proficiency).{{0,35}}{lang}",
            rf"{lang}.{{0,35}}(?:required|mandatory|must|essential|fluency|proficiency)",
            rf"(?:must|need to|required to).{{0,45}}(?:speak|write|understand).{{0,30}}{lang}",
        ]
        optional_match = any(re.search(pattern, text) for pattern in optional_patterns)
        required_match = any(re.search(pattern, text) for pattern in required_patterns)
        if optional_match:
            optional_hits.append(language)
        if required_match:
            # Phrases such as "fluent Finnish is an advantage" contain both
            # proficiency and optionality language. Optionality wins unless a
            # separate hard requirement phrase is present.
            hard_required = bool(re.search(
                rf"(?:{lang}.{{0,35}}(?:(?<!not )required|mandatory|must|essential)|(?:must|required to|need to).{{0,55}}{lang})",
                text,
            ))
            if hard_required or not optional_match:
                mandatory_hits.append(language)
    if mandatory_hits:
        return LanguageResult("LOCAL_REQUIRED", f"Required local language detected: {', '.join(mandatory_hits)}")
    if optional_hits:
        return LanguageResult("LOCAL_OPTIONAL", f"Local language is optional: {', '.join(optional_hits)}")
    english_explicit = bool(re.search(r"\benglish\b", text))
    english_text_signals = sum(token in text for token in ("the ", "and ", "you ", "we ", "experience", "skills", "team"))
    if english_explicit:
        return LanguageResult("ENGLISH_COMPATIBLE", "English mentioned and no mandatory local language detected")
    if english_text_signals >= 4:
        return LanguageResult("ENGLISH_COMPATIBLE", "Posting is in English and no mandatory local language requirement was detected")
    return LanguageResult("UNCLEAR", "Working language could not be established")


def classify_role(title: str, description: str) -> str:
    text = normalize_text(f"{title} {description[:1200]}")
    for family, patterns in ROLE_PATTERNS:
        if any(pattern in text for pattern in patterns):
            return family
    return "Other"


def extract_skills(text: str) -> list[str]:
    normalized = f" {normalize_text(text)} "
    found: list[str] = []
    for canonical, aliases in SKILL_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            found.append(canonical)
    return sorted(set(found))


def role_similarity(title: str, profile: CandidateProfile) -> float:
    normalized_title = normalize_text(title)
    if any(role in normalized_title or normalized_title in role for role in profile.preferred_roles):
        return 1.0
    tokens = set(normalized_title.split())
    best = 0.0
    for role in profile.preferred_roles:
        role_tokens = set(normalize_text(role).split())
        if not role_tokens:
            continue
        overlap = len(tokens & role_tokens) / len(role_tokens)
        best = max(best, overlap)
    return min(best, 1.0)

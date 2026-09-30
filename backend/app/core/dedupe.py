from app.core.text import normalize_text, normalized_key, text_similarity


def content_hash(company: str, title: str, location: str) -> str:
    return normalized_key(company, title, location)


def _location_match(a: str, b: str) -> bool:
    first = normalize_text(a)
    second = normalize_text(b)
    if not first or not second:
        return True
    if first in second or second in first:
        return True
    return text_similarity(first, second) >= 0.62


def probable_duplicate(
    company_a: str,
    title_a: str,
    location_a: str,
    company_b: str,
    title_b: str,
    location_b: str,
) -> bool:
    company_match = text_similarity(company_a, company_b) >= 0.9
    title_match = text_similarity(title_a, title_b) >= 0.9
    return company_match and title_match and _location_match(location_a, location_b)

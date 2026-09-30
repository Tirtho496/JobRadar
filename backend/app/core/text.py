import hashlib
import html
import re
import unicodedata
from difflib import SequenceMatcher

from bs4 import BeautifulSoup


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    soup = BeautifulSoup(html.unescape(value), "html.parser")
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()


def normalize_text(value: str | None) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = re.sub(r"[^a-z0-9+#./ -]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalized_key(company: str, title: str, location: str) -> str:
    company_n = normalize_text(company)
    title_n = re.sub(r"\b(junior|jr\.?|new|hiring)\b", "", normalize_text(title))
    location_n = normalize_text(location)
    location_n = re.sub(r"\b(finland|sweden|norway|netherlands|suomi|sverige|norge|nederland)\b", "", location_n)
    location_n = re.sub(r"\s+", " ", location_n).strip(" ,-/")
    raw = f"{company_n}|{title_n.strip()}|{location_n}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()

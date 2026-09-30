from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

from app.config import get_settings


class Constraints(BaseModel):
    max_required_years: int = 3
    borderline_required_years: int = 4
    reject_senior_titles: bool = True
    require_english_compatible: bool = True
    allow_local_language_optional: bool = True


class CandidateProfile(BaseModel):
    name: str
    headline: str
    experience_level: str
    commercial_experience_years: float
    summary: str
    preferred_roles: list[str]
    skills: list[str]
    domain_strengths: list[str]
    constraints: Constraints


class CountryConfig(BaseModel):
    code: str
    cities: list[str]
    local_languages: list[str]
    aliases: list[str] = []


class LocationsConfig(BaseModel):
    countries: dict[str, CountryConfig]
    remote_eu: bool = True


def _read_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


@lru_cache
def get_profile() -> CandidateProfile:
    settings = get_settings()
    return CandidateProfile.model_validate(_read_yaml(settings.config_dir / "profile.yaml"))


@lru_cache
def get_locations() -> LocationsConfig:
    settings = get_settings()
    return LocationsConfig.model_validate(_read_yaml(settings.config_dir / "locations.yaml"))


@lru_cache
def get_sources_config() -> dict:
    return _read_yaml(get_settings().config_dir / "sources.yaml")


@lru_cache
def get_companies_config() -> dict:
    return _read_yaml(get_settings().config_dir / "companies.yaml")

from typing import Any

from app.collectors.base import BaseCollector, RawJob, parse_datetime
from app.core.text import strip_html


class PlatsbankenCollector(BaseCollector):
    name = "platsbanken"
    base_url = "https://jobsearch.api.jobtechdev.se/search"

    def __init__(self, search_terms: list[str]) -> None:
        super().__init__()
        self.search_terms = search_terms

    async def collect(self) -> list[RawJob]:
        jobs: dict[str, RawJob] = {}
        for term in self.search_terms:
            data = await self.get_json(self.base_url, params={"q": term, "limit": 100, "offset": 0})
            for item in data.get("hits", []):
                job_id = str(item.get("id") or item.get("external_id") or item.get("webpage_url"))
                employer = item.get("employer") or {}
                address = item.get("workplace_address") or {}
                description = item.get("description") or {}
                location_parts = [
                    address.get("city"),
                    address.get("municipality"),
                    address.get("region"),
                    address.get("country"),
                ]
                jobs[job_id] = RawJob(
                    source=self.name,
                    source_job_id=job_id,
                    url=item.get("webpage_url") or (item.get("application_details") or {}).get("url") or "",
                    title=item.get("headline") or "Untitled role",
                    company=employer.get("name") or employer.get("workplace") or "Unknown employer",
                    location=", ".join(part for part in location_parts if part),
                    description=strip_html(description.get("text_formatted") or description.get("text") or ""),
                    date_posted=parse_datetime(item.get("publication_date")),
                    deadline=parse_datetime(item.get("application_deadline")),
                    remote="remote" in str(item.get("workplace_model", "")).lower(),
                    metadata={"query": term},
                )
        return list(jobs.values())


class JobbnorgeCollector(BaseCollector):
    name = "jobbnorge"
    base_url = "https://publicapi.jobbnorge.no/v1/Jobs"

    async def collect(self) -> list[RawJob]:
        data = await self.get_json(self.base_url)
        items: list[dict[str, Any]]
        if isinstance(data, list):
            items = data
        else:
            items = data.get("jobs") or data.get("items") or data.get("results") or []
        jobs = []
        for item in items[:500]:
            job_id = str(item.get("jobId") or item.get("id") or item.get("advertisementId") or item.get("url"))
            title = item.get("title") or item.get("positionTitle") or item.get("name") or "Untitled role"
            employer = item.get("employerName") or item.get("employer") or item.get("companyName") or "Unknown employer"
            if isinstance(employer, dict):
                employer = employer.get("name") or employer.get("employerName") or "Unknown employer"
            location = item.get("municipalityName") or item.get("location") or item.get("place") or "Norway"
            if isinstance(location, dict):
                location = ", ".join(str(v) for v in location.values() if v)
            description = item.get("description") or item.get("jobDescription") or item.get("ingress") or ""
            url = (
                item.get("url")
                or item.get("jobUrl")
                or item.get("applicationUrl")
                or f"https://www.jobbnorge.no/en/available-jobs/job/{job_id}"
            )
            jobs.append(
                RawJob(
                    source=self.name,
                    source_job_id=job_id,
                    url=url,
                    title=str(title),
                    company=str(employer),
                    location=str(location),
                    description=strip_html(str(description)),
                    date_posted=parse_datetime(
                        item.get("publishedDate") or item.get("publishDate") or item.get("datePublished")
                    ),
                    deadline=parse_datetime(item.get("deadline") or item.get("applicationDeadline")),
                    remote="remote" in str(item).lower(),
                )
            )
        return jobs


class JobOpportunitiesCollector(BaseCollector):
    """Keyless public job aggregator with country-scoped title search.

    The public endpoint is intentionally queried with a small set of targeted
    role phrases. Results are deduplicated by the provider's stable job id.
    """

    name = "jobopportunities"
    base_url = "https://api.jobopportunitiesapi.org/public/jobs"

    def __init__(self, countries: dict[str, str], search_terms: list[str]) -> None:
        super().__init__()
        self.countries = countries
        self.search_terms = search_terms

    async def collect(self) -> list[RawJob]:
        jobs: dict[str, RawJob] = {}
        for country_code, country_name in self.countries.items():
            for term in self.search_terms:
                data = await self.get_json(
                    self.base_url,
                    params={
                        "country": country_code,
                        "title": term,
                        "limit": 50,
                        "include_description": "true",
                    },
                )
                items = data.get("jobs") or data.get("data") or data.get("results") or []
                for item in items:
                    job_id = str(item.get("id") or item.get("apply_url") or item.get("url") or "")
                    if not job_id:
                        continue
                    city = str(item.get("city") or "").strip()
                    raw_location = str(item.get("location") or "").strip()
                    location = raw_location or city
                    if country_name.lower() not in location.lower():
                        location = ", ".join(part for part in [location, country_name] if part)
                    remote_value = str(item.get("remote") or "").lower()
                    jobs[job_id] = RawJob(
                        source=self.name,
                        source_job_id=job_id,
                        url=item.get("apply_url") or item.get("url") or "",
                        title=item.get("title") or "Untitled role",
                        company=item.get("company") or "Unknown employer",
                        location=location,
                        description=strip_html(item.get("description") or ""),
                        date_posted=parse_datetime(item.get("posted_at") or item.get("date_posted")),
                        deadline=parse_datetime(item.get("expires_at")),
                        remote=remote_value == "remote",
                        metadata={
                            "query": term,
                            "country_code": country_code,
                            "upstream_source": item.get("source"),
                            "upstream_source_type": item.get("source_type"),
                            "remote_mode": item.get("remote"),
                        },
                    )
        return list(jobs.values())


class ArbeitnowCollector(BaseCollector):
    name = "arbeitnow"
    base_url = "https://www.arbeitnow.com/api/job-board-api"

    async def collect(self) -> list[RawJob]:
        jobs = []
        for page in range(1, 4):
            data = await self.get_json(self.base_url, params={"page": page})
            for item in data.get("data", []):
                jobs.append(
                    RawJob(
                        source=self.name,
                        source_job_id=str(item.get("slug") or item.get("url")),
                        url=item.get("url") or "",
                        title=item.get("title") or "Untitled role",
                        company=item.get("company_name") or "Unknown employer",
                        location=item.get("location") or ("Remote" if item.get("remote") else ""),
                        description=strip_html(item.get("description") or ""),
                        date_posted=parse_datetime(item.get("created_at")),
                        remote=bool(item.get("remote")),
                        metadata={"tags": item.get("tags", []), "job_types": item.get("job_types", [])},
                    )
                )
            if not data.get("links", {}).get("next"):
                break
        return jobs


class JobicyCollector(BaseCollector):
    name = "jobicy"
    base_url = "https://jobicy.com/api/v2/remote-jobs"

    async def collect(self) -> list[RawJob]:
        data = await self.get_json(self.base_url, params={"count": 200})
        items = data.get("jobs") or []
        return [
            RawJob(
                source=self.name,
                source_job_id=str(item.get("id") or item.get("url")),
                url=item.get("url") or "",
                title=item.get("jobTitle") or "Untitled role",
                company=item.get("companyName") or "Unknown employer",
                location=item.get("jobGeo") or "Remote",
                description=strip_html(item.get("jobDescription") or item.get("jobExcerpt") or ""),
                date_posted=parse_datetime(item.get("pubDate")),
                remote=True,
                metadata={"job_level": item.get("jobLevel"), "job_type": item.get("jobType")},
            )
            for item in items
        ]


class RemotiveCollector(BaseCollector):
    name = "remotive"
    base_url = "https://remotive.com/api/remote-jobs"

    async def collect(self) -> list[RawJob]:
        data = await self.get_json(self.base_url, params={"limit": 100})
        return [
            RawJob(
                source=self.name,
                source_job_id=str(item.get("id") or item.get("url")),
                url=item.get("url") or "",
                title=item.get("title") or "Untitled role",
                company=item.get("company_name") or "Unknown employer",
                location=item.get("candidate_required_location") or "Remote",
                description=strip_html(item.get("description") or ""),
                date_posted=parse_datetime(item.get("publication_date")),
                remote=True,
                metadata={"category": item.get("category"), "job_type": item.get("job_type")},
            )
            for item in data.get("jobs", [])
        ]


class RemoteOKCollector(BaseCollector):
    name = "remoteok"
    base_url = "https://remoteok.com/api"

    async def collect(self) -> list[RawJob]:
        data = await self.get_json(self.base_url)
        items = (
            data[1:]
            if isinstance(data, list) and data and "legal" in data[0]
            else data
            if isinstance(data, list)
            else []
        )
        jobs = []
        for item in items[:200]:
            jobs.append(
                RawJob(
                    source=self.name,
                    source_job_id=str(item.get("id") or item.get("url")),
                    url=item.get("url") or item.get("apply_url") or "",
                    title=item.get("position") or "Untitled role",
                    company=item.get("company") or "Unknown employer",
                    location=item.get("location") or "Remote",
                    description=strip_html(item.get("description") or ""),
                    date_posted=parse_datetime(item.get("date") or item.get("epoch")),
                    remote=True,
                    metadata={"tags": item.get("tags", [])},
                )
            )
        return jobs

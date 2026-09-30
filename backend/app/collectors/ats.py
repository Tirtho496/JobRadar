import asyncio

from app.collectors.base import BaseCollector, RawJob, parse_datetime
from app.core.text import strip_html


class LeverCollector(BaseCollector):
    name = "lever"

    def __init__(self, companies: list[dict]) -> None:
        super().__init__()
        self.companies = companies
        if len(companies) == 1:
            self.name = f"lever:{companies[0]['site']}"

    async def _company_jobs(self, company: dict) -> list[RawJob]:
        site = company["site"]
        api_host = "https://api.lever.co"
        data = await self.get_json(f"{api_host}/v0/postings/{site}", params={"mode": "json"})
        jobs = []
        for item in data if isinstance(data, list) else []:
            categories = item.get("categories") or {}
            lists_text = " ".join(entry.get("text", "") + " " + entry.get("content", "") for entry in item.get("lists", []))
            description = strip_html(" ".join(filter(None, [item.get("descriptionPlain"), item.get("description"), item.get("additionalPlain"), lists_text])))
            jobs.append(RawJob(
                source=f"lever:{site}",
                source_job_id=str(item.get("id") or item.get("hostedUrl")),
                url=item.get("hostedUrl") or item.get("applyUrl") or "",
                title=item.get("text") or "Untitled role",
                company=company.get("name") or site,
                location=categories.get("location") or "",
                description=description,
                date_posted=parse_datetime(item.get("createdAt")),
                remote=str(item.get("workplaceType", "")).lower() == "remote" or "remote" in str(categories.get("location", "")).lower(),
                metadata={"ats": "lever", "team": categories.get("team"), "commitment": categories.get("commitment")},
            ))
        return jobs

    async def collect(self) -> list[RawJob]:
        if len(self.companies) == 1:
            return await self._company_jobs(self.companies[0])
        results = await asyncio.gather(*(self._company_jobs(company) for company in self.companies), return_exceptions=True)
        jobs: list[RawJob] = []
        for result in results:
            if isinstance(result, list):
                jobs.extend(result)
        return jobs


class GreenhouseCollector(BaseCollector):
    name = "greenhouse"

    def __init__(self, companies: list[dict]) -> None:
        super().__init__()
        self.companies = companies
        if len(companies) == 1:
            self.name = f"greenhouse:{companies[0]['board']}"

    async def _company_jobs(self, company: dict) -> list[RawJob]:
        board = company["board"]
        data = await self.get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs", params={"content": "true"})
        return [RawJob(
            source=f"greenhouse:{board}",
            source_job_id=str(item.get("id") or item.get("absolute_url")),
            url=item.get("absolute_url") or "",
            title=item.get("title") or "Untitled role",
            company=company.get("name") or board,
            location=(item.get("location") or {}).get("name") or "",
            description=strip_html(item.get("content") or ""),
            date_posted=parse_datetime(item.get("updated_at")),
            remote="remote" in str((item.get("location") or {}).get("name", "")).lower(),
            metadata={"ats": "greenhouse", "language": item.get("language")},
        ) for item in data.get("jobs", [])]

    async def collect(self) -> list[RawJob]:
        if len(self.companies) == 1:
            return await self._company_jobs(self.companies[0])
        results = await asyncio.gather(*(self._company_jobs(company) for company in self.companies), return_exceptions=True)
        jobs: list[RawJob] = []
        for result in results:
            if isinstance(result, list):
                jobs.extend(result)
        return jobs


class SmartRecruitersCollector(BaseCollector):
    name = "smartrecruiters"

    def __init__(self, companies: list[dict]) -> None:
        super().__init__()
        self.companies = companies
        if len(companies) == 1:
            self.name = f"smartrecruiters:{companies[0]['identifier']}"

    async def _company_jobs(self, company: dict) -> list[RawJob]:
        identifier = company["identifier"]
        base = f"https://api.smartrecruiters.com/v1/companies/{identifier}/postings"
        data = await self.get_json(base, params={"limit": 100, "offset": 0})
        items = data.get("content") or []
        jobs = []
        for item in items:
            job_id = str(item.get("id"))
            detail = {}
            try:
                detail = await self.get_json(f"{base}/{job_id}")
            except RuntimeError:
                detail = item
            loc = detail.get("location") or item.get("location") or {}
            location = ", ".join(str(loc.get(key)) for key in ("city", "region", "country") if loc.get(key))
            sections = detail.get("jobAd") or {}
            description = " ".join(str(value) for value in sections.values() if isinstance(value, str))
            jobs.append(RawJob(
                source=f"smartrecruiters:{identifier}",
                source_job_id=job_id,
                url=detail.get("applyUrl") or detail.get("ref") or item.get("ref") or "",
                title=detail.get("name") or item.get("name") or "Untitled role",
                company=company.get("name") or identifier,
                location=location,
                description=strip_html(description),
                date_posted=parse_datetime(detail.get("releasedDate") or item.get("releasedDate")),
                remote="remote" in str(detail).lower(),
                metadata={"ats": "smartrecruiters"},
            ))
        return jobs

    async def collect(self) -> list[RawJob]:
        if len(self.companies) == 1:
            return await self._company_jobs(self.companies[0])
        results = await asyncio.gather(*(self._company_jobs(company) for company in self.companies), return_exceptions=True)
        jobs: list[RawJob] = []
        for result in results:
            if isinstance(result, list):
                jobs.extend(result)
        return jobs

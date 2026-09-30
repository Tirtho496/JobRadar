from app.collectors.ats import GreenhouseCollector, LeverCollector, SmartRecruitersCollector
from app.collectors.base import BaseCollector
from app.collectors.public_boards import (
    ArbeitnowCollector,
    JobbnorgeCollector,
    JobicyCollector,
    JobOpportunitiesCollector,
    PlatsbankenCollector,
    RemoteOKCollector,
    RemotiveCollector,
)
from app.core.profile import get_companies_config, get_sources_config


def build_collectors() -> list[BaseCollector]:
    sources = get_sources_config()
    companies = get_companies_config()
    public = sources.get("public_sources", {})
    collectors: list[BaseCollector] = []
    if public.get("platsbanken", {}).get("enabled"):
        collectors.append(PlatsbankenCollector(public["platsbanken"].get("search_terms", [])))
    if public.get("jobbnorge", {}).get("enabled"):
        collectors.append(JobbnorgeCollector())
    if public.get("jobopportunities", {}).get("enabled"):
        cfg = public["jobopportunities"]
        collectors.append(JobOpportunitiesCollector(cfg.get("countries", {}), cfg.get("search_terms", [])))
    if public.get("arbeitnow", {}).get("enabled"):
        collectors.append(ArbeitnowCollector())
    if public.get("jobicy", {}).get("enabled"):
        collectors.append(JobicyCollector())
    if public.get("remotive", {}).get("enabled"):
        collectors.append(RemotiveCollector())
    if public.get("remoteok", {}).get("enabled"):
        collectors.append(RemoteOKCollector())

    ats = sources.get("ats", {})
    if ats.get("lever") and companies.get("lever"):
        collectors.extend(LeverCollector([company]) for company in companies["lever"])
    if ats.get("greenhouse") and companies.get("greenhouse"):
        collectors.extend(GreenhouseCollector([company]) for company in companies["greenhouse"])
    if ats.get("smartrecruiters") and companies.get("smartrecruiters"):
        collectors.extend(SmartRecruitersCollector([company]) for company in companies["smartrecruiters"])
    return collectors

import pytest

from app.collectors.public_boards import JobOpportunitiesCollector


@pytest.mark.asyncio
async def test_job_opportunities_mapping():
    collector = JobOpportunitiesCollector({"DE": "Germany"}, ["software engineer"])

    async def fake_get_json(*args, **kwargs):
        return {
            "data": [{
                "id": "abc-123",
                "title": "Software Engineer",
                "company": "Example GmbH",
                "country": "DE",
                "city": "Berlin",
                "location": "Berlin",
                "remote": "hybrid",
                "posted_at": "2026-09-24T08:00:00Z",
                "expires_at": "2026-10-15T23:59:59Z",
                "apply_url": "https://example.com/apply",
                "source": "workday",
                "source_type": "ats",
                "description": "English is the working language. Build Python services.",
            }]
        }

    collector.get_json = fake_get_json  # type: ignore[method-assign]
    try:
        jobs = await collector.collect()
    finally:
        await collector.close()
    assert len(jobs) == 1
    job = jobs[0]
    assert job.source_job_id == "abc-123"
    assert job.location == "Berlin, Germany"
    assert job.company == "Example GmbH"
    assert job.deadline is not None

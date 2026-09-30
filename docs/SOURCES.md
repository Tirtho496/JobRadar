# Source policy

JobRadar uses public or documented interfaces where possible.

## Enabled

- Job Opportunities API public/keyless endpoint, queried by target country and role phrase
- Arbetsförmedlingen JobSearch / Platsbanken
- Jobbnorge Public API
- Arbeitnow job-board API
- Jobicy public remote-jobs API
- Remotive public remote-jobs API
- RemoteOK public job feed
- Greenhouse Job Board API
- Lever Postings API
- SmartRecruiters public Posting API (connector included; companies can be configured)

## Optional / not enabled by default

### Job Market Finland

Its official retrieval interface requires organisational onboarding and credentials. The application therefore does not pretend it is a no-key source.

### NAV Arbeidsplassen

NAV provides public job-ad access, but the public feed uses a rotating bearer token. It is not enabled by default in this zero-setup package.

### Commercial aggregators without unrestricted public APIs

Browser scraping is not a foundation of the default product. If a service provides a permitted feed/API later, add a connector under `backend/app/collectors/` and register it in `registry.py`.

# JobRadar

JobRadar is a local-first job intelligence platform that collects vacancies from public job APIs and company ATS feeds, normalizes and deduplicates them, applies configurable eligibility rules, ranks opportunities against a candidate profile, and supports application tracking and job-market analysis.

The project is designed as a production-oriented ML/software-engineering system rather than a one-off scraper: ingestion, ranking, persistence, evaluation, observability, API design, CI and graceful degradation are all explicit parts of the architecture.

## Why JobRadar?

General-purpose job boards optimize for discovery volume, which often means noisy recommendations, mismatched seniority levels and repeated listings across multiple sources.

JobRadar approaches the problem as a configurable ranking pipeline. It collects vacancies from multiple sources, applies explicit eligibility constraints, removes duplicates, extracts job requirements and ranks the remaining opportunities against a candidate profile.

The result is a smaller, more relevant set of opportunities while preserving transparency around why each vacancy was accepted, rejected or ranked highly.

## Highlights

- Multi-source asynchronous job ingestion
- Public job API and ATS connectors
- Configurable geography, role, language and experience rules
- Cross-source normalization and deduplication
- Deterministic ranking plus optional local sentence-transformer similarity
- Graceful fallback when semantic ranking is unavailable
- Application pipeline tracking
- Recommendation feedback and bounded personalization
- Skills-market and missing-skill analytics
- Daily digest and scheduled ingestion
- Source health, metrics and structured logging
- Offline ranking evaluation / model lab
- PostgreSQL + pgvector + Alembic
- FastAPI REST API
- React + TypeScript frontend
- Docker Compose
- GitHub Actions CI
- Unit and integration-oriented test suite
- No paid API required for the default local setup

## Architecture

```text
Public job APIs        Company ATS feeds        Remote job APIs
      |                       |                       |
      +-----------------------+-----------------------+
                              |
                       Async collectors
                              |
                retry / timeout / validation
                              |
                    normalize + geography
                              |
          language + seniority + experience gates
                              |
                    skill / role extraction
                              |
                   semantic + rule ranking
                              |
                     cross-source dedupe
                              |
                   PostgreSQL + pgvector
                              |
             +----------------+----------------+
             |                                 |
         FastAPI                           Scheduler
             |
        React dashboard
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the design rationale.

## Quick start

### Prerequisites

- Docker Desktop / Docker Engine
- Docker Compose
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Tirtho496/JobRadar.git
cd jobradar
```

### 2. Create local environment configuration

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

For anything beyond local use, change `API_KEY` and database credentials in `.env`.

### 3. Configure your search

JobRadar intentionally keeps candidate-specific settings in YAML rather than application code:

- `config/profile.yaml` — skills, target role families and eligibility rules
- `config/locations.yaml` — geography and language metadata
- `config/companies.yaml` — optional ATS company watchlists
- `config/sources.yaml` — source enablement and search terms

The committed files contain example values only. See [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) for a private local-override workflow that keeps personal settings out of Git.

### 4. Start JobRadar

Windows:

```powershell
.\scripts\start.ps1
```

or double-click:

```text
START_JOBRADAR.bat
```

macOS/Linux:

```bash
./scripts/start.sh
```

Then open:

```text
Web UI:    http://localhost:8080
API docs:  http://localhost:8000/docs
```

The first build may download the configured local embedding model. If the model cannot load, JobRadar continues with deterministic ranking.

## How ranking works

JobRadar separates eligibility from relevance. Hard constraints are evaluated before similarity scoring, so semantic similarity cannot silently override a configured language, seniority or experience rule.

A typical ranking pipeline is:

1. geography / remote eligibility
2. language compatibility
3. seniority and explicit experience requirements
4. role-family similarity
5. technical skill overlap
6. optional semantic similarity
7. domain overlap
8. recency and application-value adjustment

Scoring weights and hard constraints are configurable in the candidate profile.

## Source strategy

The collector layer prefers stable, documented interfaces:

1. official public APIs
2. public ATS/job-board APIs
3. documented public feeds
4. other permitted public sources

Browser scraping of commercial boards is deliberately not the foundation of the system. Each source is isolated behind a collector interface with its own timeout, retry and health telemetry, so one failing provider does not stop the complete ingestion run.

See [`docs/SOURCES.md`](docs/SOURCES.md).

## Evaluation

The model lab supports offline ranking evaluation against labelled vacancies. The repository includes only a small illustrative smoke dataset; meaningful portfolio metrics should be generated from a larger manually labelled dataset.

Useful metrics include:

- Precision@K
- NDCG@K
- classification accuracy for eligibility rules
- duplicate-removal rate
- source success rate
- ranking latency

See [`docs/EVALUATION.md`](docs/EVALUATION.md).

## Observability and reliability

JobRadar includes:

- structured application logs
- source-level ingestion telemetry
- retries with backoff and request timeouts
- `/health` and `/ready` endpoints
- metrics endpoint
- graceful semantic-model fallback
- source isolation
- persistent ingestion/model-run records

Health endpoints:

```text
GET /health
GET /ready
GET /metrics
```

## Development

Backend:

```bash
cd backend
pip install -r requirements.txt
ruff check app tests
pytest
```

Frontend:

```bash
cd frontend
npm install
npm run build
```

Database migrations:

```bash
cd backend
alembic upgrade head
```

Full stack:

```bash
docker compose up --build
```

## Project structure

```text
jobradar/
├── backend/                 FastAPI application, ranking and collectors
├── frontend/                React/TypeScript web application
├── config/                  Public example configuration
├── data/evaluation/         Illustrative evaluation data
├── docs/                    Architecture, sources, configuration, evaluation
├── scripts/                 Local start/stop helpers
├── .github/workflows/       CI pipeline
├── docker-compose.yml
└── README.md
```

## Privacy

The public repository should contain only generic example configuration. Personal candidate settings, target locations, company watchlists and labelled evaluation data can be stored in `config.local/` and `data.local/`, both of which are ignored by Git.

No external paid LLM service is required by default, and recommendation feedback remains local unless the deployment is explicitly changed.

## Design philosophy

JobRadar is intentionally implemented as a modular monolith. At the current workload, introducing Kafka, Kubernetes or multiple deployable services would increase operational complexity without improving the product. Internal boundaries keep collectors, ranking, persistence and API logic separable if future scale justifies decomposition.

## Roadmap

Potential future extensions include richer ranking personalization, candidate-document version selection, expanded source adapters and assisted application workflows.

## License — MIT

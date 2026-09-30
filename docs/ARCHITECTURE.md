# Architecture

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
                   + feedback preference bias
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

## Design decisions

### Modular monolith

The expected workload is small enough that splitting ingestion, ranking and API into separate deployable services would add operational burden without improving reliability. Internal modules have explicit boundaries so they can be extracted later if real scale justifies it.

### PostgreSQL + pgvector

SQLite would be enough for one user, but PostgreSQL is used deliberately to exercise production persistence, migrations, concurrency and vector storage while remaining free through Docker.

### Local model with deterministic fallback

The sentence-transformer provider runs locally. If the model cannot load, deterministic lexical/skill scoring remains available and the system keeps operating.

### Source isolation

Every connector has independent timeout, retry and source-run telemetry. One failed provider cannot fail the complete daily scan.

### No paid dependencies

No feature requires a paid LLM, paid vector database or paid hosting service.

### Feedback personalization

Recommendation feedback is not sent to an external service. After at least three feedback labels exist, JobRadar derives bounded role/skill preferences and applies at most a ±5-point adjustment during the next ingestion run. The deterministic eligibility gates still dominate: feedback cannot make a senior or mandatory-local-language vacancy eligible.

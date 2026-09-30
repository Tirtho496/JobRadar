# Evaluation strategy

The included `job_relevance_v1.jsonl` is a small smoke set. Replace it over time with real jobs you personally label.

Suggested labels:

```json
{"title":"...","description":"...","relevant":1}
```

A stronger V1.5 dataset should add structured labels for:

- relevant / irrelevant
- too senior
- local language required
- wrong geography
- role mismatch
- experience mismatch
- strong match / borderline

Use recommendation feedback from the dashboard as a source of future labels, but review those labels before treating them as an evaluation gold set.

JobRadar currently reports Precision@10, NDCG@10 and mean per-document scoring latency in Model Lab.

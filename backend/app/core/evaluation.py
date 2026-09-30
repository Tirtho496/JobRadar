import json
import math
import time
from pathlib import Path

from app.core.embedding import EmbeddingService, lexical_similarity
from app.core.profile import CandidateProfile


def _dcg(labels: list[int], k: int) -> float:
    return sum(label / math.log2(index + 2) for index, label in enumerate(labels[:k]))


def _metrics(scored: list[tuple[float, int]], k: int = 10) -> tuple[float, float]:
    ranked = sorted(scored, key=lambda item: item[0], reverse=True)
    top = ranked[:k]
    precision = sum(label for _, label in top) / max(len(top), 1)
    ideal = sorted((label for _, label in scored), reverse=True)
    ndcg = _dcg([label for _, label in ranked], k) / max(_dcg(ideal, k), 1e-9)
    return precision, ndcg


def load_dataset(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def evaluate(profile: CandidateProfile, embedding_service: EmbeddingService, dataset_path: Path) -> list[dict]:
    rows = load_dataset(dataset_path)
    profile_text = f"{profile.summary} {' '.join(profile.preferred_roles)} {' '.join(profile.skills)}"
    results = []

    start = time.perf_counter()
    lexical_scored = [(lexical_similarity(profile_text, f"{row['title']} {row['description']}"), int(row['relevant'])) for row in rows]
    lexical_latency = (time.perf_counter() - start) * 1000 / max(len(rows), 1)
    p10, n10 = _metrics(lexical_scored)
    results.append({"model_name": "lexical-jaccard", "precision_at_10": p10, "ndcg_at_10": n10, "mean_latency_ms": lexical_latency, "notes": "Deterministic fallback baseline"})

    start = time.perf_counter()
    texts = [profile_text] + [f"{row['title']} {row['description']}" for row in rows]
    vectors = embedding_service.encode(texts)
    if vectors:
        import numpy as np

        base = np.asarray(vectors[0])
        scored = [(float(np.dot(base, np.asarray(vector))), int(row["relevant"])) for vector, row in zip(vectors[1:], rows)]
        latency = (time.perf_counter() - start) * 1000 / max(len(rows), 1)
        p10, n10 = _metrics(scored)
        results.append({"model_name": embedding_service.model_name, "precision_at_10": p10, "ndcg_at_10": n10, "mean_latency_ms": latency, "notes": "Local sentence-transformer embedding model"})
    return results

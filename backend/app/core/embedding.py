import logging
import threading
from functools import lru_cache

import numpy as np

from app.config import get_settings
from app.core.text import normalize_text

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    def __init__(self) -> None:
        self._model = None
        self.available = False
        self.model_name = settings.embedding_model
        self._load_attempted = False
        self._load_lock = threading.Lock()

    def _load(self) -> None:
        if self._model is not None or self._load_attempted or not settings.embedding_enabled:
            return
        with self._load_lock:
            if self._model is not None or self._load_attempted:
                return
            self._load_attempted = True
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(settings.embedding_model, device=settings.embedding_device)
                self.available = True
                logger.info("embedding model loaded", extra={"source": settings.embedding_model})
            except Exception:
                self.available = False
                logger.exception("embedding model unavailable; deterministic fallback active")

    def encode(self, texts: list[str]) -> list[list[float]] | None:
        self._load()
        if not self.available or self._model is None:
            return None
        vectors = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [vector.astype(float).tolist() for vector in vectors]

    def similarity(self, a: str, b: str) -> float:
        vectors = self.encode([a, b])
        if vectors:
            first = np.asarray(vectors[0])
            second = np.asarray(vectors[1])
            return float(np.dot(first, second))
        return lexical_similarity(a, b)


def lexical_similarity(a: str, b: str) -> float:
    a_tokens = set(normalize_text(a).split())
    b_tokens = set(normalize_text(b).split())
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()

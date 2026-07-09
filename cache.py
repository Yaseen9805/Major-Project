"""In-memory semantic cache used by the adaptive handler (Setup B)."""

import time

import numpy as np
from sentence_transformers import SentenceTransformer

from config import CACHE_SIMILARITY_THRESHOLD, EMBEDDING_MODEL_NAME

_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def embed(text: str) -> np.ndarray:
    vector = _get_model().encode(text, normalize_embeddings=True)
    return np.asarray(vector, dtype=np.float32)


class SemanticCache:
    """Cosine-similarity cache over an in-memory list of entries.

    Fine for the ~100-1000 entries this prototype deals with; a real vector
    store (Qdrant/FAISS) would replace this at larger scale.
    """

    def __init__(self, threshold: float = CACHE_SIMILARITY_THRESHOLD):
        self.threshold = threshold
        self._entries = []  # list of dicts: embedding, query_text, answer, tier_used, timestamp

    def check(self, query: str) -> dict | None:
        if not self._entries:
            return None

        query_embedding = embed(query)
        embeddings = np.stack([entry["embedding"] for entry in self._entries])
        similarities = embeddings @ query_embedding  # embeddings are normalized -> cosine sim

        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        if best_score >= self.threshold:
            match = self._entries[best_idx]
            return {
                "answer": match["answer"],
                "tier_used": match["tier_used"],
                "matched_query": match["query_text"],
                "similarity": best_score,
            }
        return None

    def add(self, query: str, answer: str, tier_used: str) -> None:
        self._entries.append(
            {
                "embedding": embed(query),
                "query_text": query,
                "answer": answer,
                "tier_used": tier_used,
                "timestamp": time.time(),
            }
        )

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)


# Module-level default cache instance + functional API, matching the plan's
# `check_cache` / `add_to_cache` naming.
_default_cache = SemanticCache()


def check_cache(query: str, threshold: float = CACHE_SIMILARITY_THRESHOLD) -> dict | None:
    _default_cache.threshold = threshold
    return _default_cache.check(query)


def add_to_cache(query: str, answer: str, tier_used: str) -> None:
    _default_cache.add(query, answer, tier_used)


def clear_cache() -> None:
    _default_cache.clear()

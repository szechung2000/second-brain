"""Index-only query path: it intentionally has no vault or source arguments."""

from second_brain.memory import MemoryAdapter


def query(text: str, *, memory: MemoryAdapter, scopes: list[str], k: int) -> list[dict]:
    return [_query_result(hit) for hit in memory.recall(text, scopes=scopes, k=k)]


def _query_result(hit: dict) -> dict:
    metadata = hit.get("metadata") or {}
    citation = metadata.get("citation") or {}
    locator = citation.get("locator")
    if not locator and metadata.get("page_start"):
        locator = f"p. {metadata['page_start']}"
    return {
        "content": hit.get("content", ""),
        "id": hit.get("id"),
        "locator": locator or "unknown",
        "namespace": hit.get("namespace", "unknown"),
        "score": hit.get("score", 0),
        "source_id": metadata.get("document_id") or metadata.get("source_id") or "unknown",
    }

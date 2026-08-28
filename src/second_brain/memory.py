"""Small provider-neutral adapter for the agent-memory HTTP contract."""

from __future__ import annotations

import json
from typing import Protocol
from urllib.parse import quote
from urllib.request import Request, urlopen


class MemoryAdapter(Protocol):
    def upsert(self, external_id: str, memory: dict) -> str: ...

    def recall(self, text: str, *, scopes: list[str], k: int) -> list[dict]: ...


class AgentMemoryAdapter:
    """Adapter for agent-memory's keyed HTTP API.

    The service itself can use SQLite, keeping this client provider-neutral and
    avoiding a second retrieval database.
    """

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def upsert(self, external_id: str, memory: dict) -> str:
        response = self._request(
            "PUT",
            f"/v1/memories/{quote(external_id, safe='')}",
            memory,
        )
        return response["id"]

    def recall(self, text: str, *, scopes: list[str], k: int) -> list[dict]:
        hits: list[dict] = []
        for scope in scopes:
            hits.extend(
                self._request("POST", "/recall", {"query": text, "namespace": scope, "k": k})
            )
        return sorted(hits, key=lambda hit: (-float(hit.get("score", 0)), hit.get("id", "")))[:k]

    def _request(self, method: str, path: str, payload: dict) -> dict | list[dict]:
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        request = Request(
            f"{self.base_url}{path}",
            data=encoded,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=30) as response:  # noqa: S310 - caller provides endpoint
            return json.loads(response.read().decode("utf-8"))

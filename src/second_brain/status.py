"""Read registered source state without touching the retrieval query path."""

from __future__ import annotations

import json
from pathlib import Path


def source_status(source_id: str, *, vault: Path) -> dict:
    if not source_id.startswith("sha256:"):
        raise ValueError("source id must start with sha256:")
    source_hash = source_id.removeprefix("sha256:")
    path = vault / "corpus" / source_hash / "v1" / "manifest.json"
    if not path.exists():
        raise FileNotFoundError(source_id)
    return json.loads(path.read_text(encoding="utf-8"))

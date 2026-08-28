"""Explicit promotion of human-verified atomic notes into the brain index."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from second_brain.frontmatter import read_frontmatter
from second_brain.memory import MemoryAdapter


class SyncRejected(ValueError):
    pass


@dataclass(frozen=True)
class SyncResult:
    memory_id: str
    external_id: str

    def as_dict(self) -> dict:
        return {"memory_id": self.memory_id, "external_id": self.external_id, "status": "synced"}


def sync_atomic_note(note: Path, *, vault: Path, actor: str, memory: MemoryAdapter) -> SyncResult:
    metadata, body = read_frontmatter(note)
    if metadata.get("type") != "atomic-memory" or metadata.get("status") != "verified":
        raise SyncRejected("only type: atomic-memory notes with status: verified may enter brain")
    relative = note.resolve().relative_to(vault.resolve()).as_posix()
    external_id = f"obsidian:{relative}"
    memory_id = memory.upsert(
        external_id,
        {
            "content": body.strip(),
            "namespace": "brain",
            "agent_id": actor,
            "title": _title(body),
            "metadata": {
                "actor": actor,
                "note_path": relative,
                "provenance": metadata.get("provenance"),
            },
        },
    )
    return SyncResult(memory_id, external_id)


def _title(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None

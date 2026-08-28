import builtins

import pytest

from second_brain.query import query
from second_brain.sync import SyncRejected, sync_atomic_note


class RecordingMemory:
    def __init__(self):
        self.recall_calls = []
        self.writes = []

    def recall(self, text, *, scopes, k):
        self.recall_calls.append((text, scopes, k))
        return [
            {
                "id": "evidence-1",
                "namespace": "paper-corpus",
                "score": 0.8,
                "metadata": {"document_id": "sha256:unknown", "page_start": 3},
            }
        ]

    def upsert(self, external_id, memory):
        self.writes.append((external_id, memory))
        return "memory-1"


def test_query_only_uses_the_memory_adapter(monkeypatch):
    memory = RecordingMemory()

    def fail_open(*args, **kwargs):
        raise AssertionError("query must not open Markdown or PDF files")

    monkeypatch.setattr(builtins, "open", fail_open)
    assert query("What are the assumptions?", memory=memory, scopes=["paper-corpus"], k=5) == [
        {
            "content": "",
            "id": "evidence-1",
            "locator": "p. 3",
            "namespace": "paper-corpus",
            "score": 0.8,
            "source_id": "sha256:unknown",
        }
    ]
    assert memory.recall_calls == [("What are the assumptions?", ["paper-corpus"], 5)]


def test_sync_only_allows_verified_atomic_memories_and_is_keyed(tmp_path):
    note = tmp_path / "Atomic" / "claim.md"
    note.parent.mkdir()
    note.write_text("---\ntype: atomic-memory\nstatus: proposed\n---\n\n# Claim\n\nUseful fact.\n")
    memory = RecordingMemory()

    with pytest.raises(SyncRejected, match="verified"):
        sync_atomic_note(note, vault=tmp_path, actor="human", memory=memory)

    note.write_text(note.read_text().replace("status: proposed", "status: verified"))
    first = sync_atomic_note(note, vault=tmp_path, actor="human", memory=memory)
    second = sync_atomic_note(note, vault=tmp_path, actor="human", memory=memory)
    assert first.memory_id == second.memory_id == "memory-1"
    assert [key for key, _ in memory.writes] == [
        "obsidian:Atomic/claim.md",
        "obsidian:Atomic/claim.md",
    ]
    assert memory.writes[0][1]["namespace"] == "brain"
    assert memory.writes[0][1]["metadata"]["actor"] == "human"

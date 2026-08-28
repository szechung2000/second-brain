import hashlib
import json

from second_brain.ingest import ingest_pdf


class RecordingMemory:
    def __init__(self):
        self.writes = []

    def upsert(self, external_id, memory):
        self.writes.append((external_id, memory))
        return f"memory-{len(self.writes)}"


def test_ingest_creates_versioned_page_artifacts_and_source_scoped_evidence(tmp_path):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"minimal pdf source")
    memory = RecordingMemory()

    result = ingest_pdf(
        pdf,
        vault=tmp_path / "vault",
        actor="human",
        memory=memory,
        extractor=lambda _: ["Bounded inputs are required.", "Results are stable."],
    )

    source_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()
    assert result.source_id == f"sha256:{source_hash}"
    assert (tmp_path / "vault" / "sources" / f"{source_hash}.pdf").read_bytes() == pdf.read_bytes()
    assert result.run_path.is_file()
    assert json.loads(result.run_path.read_text())["source_id"] == result.source_id
    manifest = json.loads(result.manifest_path.read_text())
    assert manifest["artifact_version"] == 1
    assert manifest["page_count"] == 2
    assert manifest["extractor"]["name"] == "pypdf"
    pages = json.loads(result.pages_path.read_text())
    assert [page["page"] for page in pages["pages"]] == [1, 2]
    assert [key for key, _ in memory.writes] == [
        f"sha256:{source_hash}:page:1:chunk:0",
        f"sha256:{source_hash}:page:2:chunk:0",
    ]
    assert memory.writes[0][1]["namespace"] == "paper-corpus"
    assert memory.writes[0][1]["metadata"]["citation"]["locator"] == "p. 1"
    note = result.note_path.read_text()
    assert "review_status: unreviewed" in note
    assert note.count("## Evidence") == 1


def test_reingest_is_idempotent_and_never_overwrites_an_approved_note(tmp_path):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"minimal pdf source")
    memory = RecordingMemory()
    kwargs = {
        "vault": tmp_path / "vault",
        "actor": "codex",
        "memory": memory,
        "extractor": lambda _: ["A source claim."],
    }

    first = ingest_pdf(pdf, **kwargs)
    second = ingest_pdf(pdf, **kwargs)
    assert second.note_path.read_text() == first.note_path.read_text()
    assert len(memory.writes) == 2  # keyed adapter converges both runs

    approved = first.note_path.read_text().replace(
        "review_status: unreviewed", "review_status: approved"
    )
    first.note_path.write_text(approved)
    protected = ingest_pdf(pdf, **kwargs)
    assert protected.note_status == "protected"
    assert protected.note_path.read_text() == approved


def test_empty_extraction_is_recorded_as_blocked(tmp_path):
    pdf = tmp_path / "empty.pdf"
    pdf.write_bytes(b"empty pdf source")

    result = ingest_pdf(
        pdf,
        vault=tmp_path / "vault",
        actor="agy",
        memory=RecordingMemory(),
        extractor=lambda _: ["", "  "],
    )

    assert result.status == "blocked"
    assert result.indexed_chunks == 0
    assert json.loads(result.manifest_path.read_text())["status"] == "blocked"

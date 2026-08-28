"""Explicit, page-aware ingestion of one ordinary text-layer PDF."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from second_brain.frontmatter import read_frontmatter
from second_brain.memory import MemoryAdapter

ARTIFACT_VERSION = 1
EXTRACTOR_NAME = "pypdf"


@dataclass(frozen=True)
class IngestResult:
    source_id: str
    status: str
    manifest_path: Path
    pages_path: Path
    run_path: Path
    note_path: Path
    indexed_chunks: int
    note_status: str

    def as_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "status": self.status,
            "manifest_path": str(self.manifest_path),
            "pages_path": str(self.pages_path),
            "run_path": str(self.run_path),
            "note_path": str(self.note_path),
            "indexed_chunks": self.indexed_chunks,
            "note_status": self.note_status,
        }


def extract_pdf_pages(pdf: Path) -> list[str]:
    """Extract each text layer page separately; scanned documents stay blocked."""
    from pypdf import PdfReader

    return [(page.extract_text() or "").strip() for page in PdfReader(str(pdf)).pages]


def ingest_pdf(
    pdf: Path,
    *,
    vault: Path,
    actor: str,
    memory: MemoryAdapter,
    extractor: Callable[[Path], list[str]] = extract_pdf_pages,
) -> IngestResult:
    """Register a PDF, persist a versioned extraction, and index page evidence."""
    pdf = pdf.resolve()
    source_hash = _sha256(pdf)
    source_id = f"sha256:{source_hash}"
    source_copy = vault / "sources" / f"{source_hash}.pdf"
    source_copy.parent.mkdir(parents=True, exist_ok=True)
    if not source_copy.exists():
        shutil.copyfile(pdf, source_copy)
    elif _sha256(source_copy) != source_hash:
        raise RuntimeError(f"immutable source collision at {source_copy}")

    corpus_dir = vault / "corpus" / source_hash / f"v{ARTIFACT_VERSION}"
    manifest_path = corpus_dir / "manifest.json"
    pages_path = corpus_dir / "pages.json"
    run_path = vault / "runs" / f"{source_hash}-v{ARTIFACT_VERSION}.json"
    note_path = vault / "Literature" / f"sha256-{source_hash}.md"
    pages = extractor(source_copy)
    nonempty = [(number, text) for number, text in enumerate(pages, start=1) if text.strip()]
    status = "extracted" if nonempty else "blocked"
    manifest = {
        "artifact_version": ARTIFACT_VERSION,
        "document_id": source_id,
        "extractor": {"name": EXTRACTOR_NAME, "version": _pypdf_version()},
        "page_count": len(pages),
        "source_path": str(source_copy.relative_to(vault)),
        "source_sha256": source_hash,
        "status": status,
        "warnings": [] if nonempty else ["empty text extraction; OCR is not available in MVP"],
    }
    page_artifact = {
        "artifact_version": ARTIFACT_VERSION,
        "document_id": source_id,
        "pages": [{"page": page, "text": text} for page, text in nonempty],
    }
    _atomic_json(manifest_path, manifest)
    _atomic_json(pages_path, page_artifact)
    _atomic_json(
        run_path,
        {
            "artifact_version": ARTIFACT_VERSION,
            "corpus_path": str(corpus_dir.relative_to(vault)),
            "source_id": source_id,
            "status": status,
        },
    )
    note_status = _write_literature_note(note_path, manifest, actor)

    if not nonempty:
        return IngestResult(
            source_id, "blocked", manifest_path, pages_path, run_path, note_path, 0, note_status
        )

    for page, text in nonempty:
        external_id = f"{source_id}:page:{page}:chunk:0"
        memory.upsert(
            external_id,
            {
                "content": text,
                "namespace": "paper-corpus",
                "agent_id": actor,
                "title": pdf.stem,
                "metadata": {
                    "actor": actor,
                    "citation": {"label": f"{pdf.stem}, p. {page}", "locator": f"p. {page}"},
                    "document_id": source_id,
                    "document_version": f"{source_id}:corpus:v{ARTIFACT_VERSION}",
                    "page_end": page,
                    "page_start": page,
                    "source_sha256": source_hash,
                    "source_type": "pdf",
                },
            },
        )
    return IngestResult(
        source_id,
        "extracted",
        manifest_path,
        pages_path,
        run_path,
        note_path,
        len(nonempty),
        note_status,
    )


def _write_literature_note(note_path: Path, manifest: dict, actor: str) -> str:
    if note_path.exists() and read_frontmatter(note_path)[0].get("review_status") == "approved":
        return "protected"
    title = Path(manifest["source_path"]).stem
    note = f"""---
type: literature-note
source_id: {manifest["document_id"]}
title: {title}
source_sha256: {manifest["source_sha256"]}
source_path: {manifest["source_path"]}
corpus_path: corpus/{manifest["source_sha256"]}/v{ARTIFACT_VERSION}
extraction_version: {ARTIFACT_VERSION}
source_status: {manifest["status"]}
review_status: unreviewed
promotion_status: blocked
actor: {actor}
---

# {title}

> Generated evidence scaffold. Verify claims against the source before treating
> them as authoritative.

## Why I saved this

- Add the reason this source matters.

## Evidence

- Indexed page-aware source evidence. Review status: {manifest["status"]}.

## Review queue

- [ ] Verify important claims against cited pages.
- [ ] Promote only verified atomic notes.
"""
    _atomic_text(note_path, note)
    return "written"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _pypdf_version() -> str:
    try:
        from pypdf import __version__
    except ImportError:
        return "unavailable"
    return __version__


def _atomic_json(path: Path, value: dict) -> None:
    _atomic_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temp:
        temp.write(text)
        temp_path = Path(temp.name)
    os.replace(temp_path, path)

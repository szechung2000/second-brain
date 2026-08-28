# PRD-001: Indexed Obsidian Second Brain MVP

**Status:** Approved for implementation
**Feature:** 001 — indexed source ingestion and retrieval
**Owner:** Simon

## Problem

Obsidian is the human interface for Simon's second brain, but asking a question
should not require an LLM or agent to recursively scan every Markdown note and
PDF. The system needs a rebuildable retrieval projection powered by the sibling
`agent-memory` project.

## Product outcome

A user can explicitly ingest one technical PDF, receive a provenance-bearing
Obsidian literature-note scaffold, and ask a question through a CLI that
retrieves cited evidence from `agent-memory` without reading files at query time.

## In scope

- Explicit-path ingestion of one text-layer PDF.
- Immutable source copy and SHA-256 identity.
- Page-aware Tier-1 extraction and versioned corpus artifacts.
- Provenance-bearing chunks indexed into `agent-memory` under `paper-corpus`.
- Deterministic Obsidian literature-note scaffold with review state.
- Query command using only the `agent-memory` index.
- Verified atomic-note synchronization into `brain`.
- Idempotent reruns and safe protection of approved notes.
- Offline SQLite demo path; no provider-specific worker SDK.

## Out of scope for MVP

- OCR and scanned PDFs.
- Reliable layout reconstruction for difficult dual-column documents.
- Full equation/table/figure semantic extraction.
- Background filesystem watchers.
- Automatic claim promotion or autonomous publishing.
- A visual Kanban UI; frontmatter state is sufficient initially.
- A second vector database.

Complex documents must receive a visible review/blocked state rather than being
silently treated as trusted knowledge.

## User experience

```bash
sb ingest sources/paper.pdf --vault ./vault --actor human --json
sb status sha256:<source-hash> --json
sb query "What assumptions does the method make?" \
  --scope paper-corpus --k 5 --json
sb sync-atomic vault/Atomic/claim.md --actor human --json
sb query "How does this apply to my project?" \
  --scope brain --scope paper-corpus --k 5 --json
```

The query result must include source ID, namespace, score, and page/section
locator. It must not discover, parse, or open `.md` or `.pdf` files.

## Requirements

- `P0-1`: Source identity is a byte-level SHA-256.
- `P0-2`: Original PDFs are never overwritten.
- `P0-3`: Corpus artifacts include page boundaries and extractor/version data.
- `P0-4`: Every indexed chunk has document identity, page range, and citation.
- `P0-5`: Evidence is indexed in `paper-corpus`, never directly in `brain`.
- `P0-6`: Generated notes start unreviewed and cannot overwrite approved notes.
- `P0-7`: Only `type: atomic-memory`, `status: verified` notes can enter `brain`.
- `P0-8`: Repeating ingestion or synchronization is idempotent.
- `P0-9`: CLI output supports stable machine-readable JSON.
- `P0-10`: A failed or empty extraction is nonzero and visibly blocked.
- `P0-11`: Actor metadata supports `human`, `claude`, `codex`, and `agy` without
  provider-specific behavior.

## Definition of done

1. A sample PDF creates source, corpus, run, note, and indexed evidence artifacts.
2. Retrieval returns the relevant page citation through `agent-memory`.
3. Query-time filesystem scanning is covered by a regression test.
4. Repeated runs do not create duplicate records or duplicate note sections.
5. Unverified atomic notes are rejected from `brain`.
6. Verified atomic notes are searchable in `brain`.
7. Independent verification passes the full repository checks and this PRD.

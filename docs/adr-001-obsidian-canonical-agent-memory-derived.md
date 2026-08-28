# ADR-001: Obsidian Canonical, agent-memory Derived

**Status:** Accepted for Feature 001
**Date:** 2026-08-28

## Context

Obsidian is the primary interface and human-owned knowledge base. The system
must answer questions across notes and technical PDFs without recursively
scanning files at question time. The sibling `agent-memory` repository already
provides embedding, hybrid retrieval, namespaces, and context assembly, but its
current ingestion path needs stronger source identity and idempotency guarantees
for this integration.

## Decision

1. Keep original PDFs and reviewed Obsidian Markdown as canonical user assets.
2. Keep extracted, page-aware corpus artifacts as versioned machine evidence.
3. Treat `agent-memory` as a rebuildable retrieval projection, not the canonical
   knowledge base.
4. Index raw source evidence only under `paper-corpus` or `book-corpus`.
5. Keep generated summaries and candidate claims under `agent-derived`.
6. Promote only explicitly verified atomic notes into `brain`.
7. Use stable external IDs and source-scoped upserts so retries converge and
   identical passages in different sources retain separate provenance.
8. Expose provider-neutral actor metadata (`human`, `claude`, `codex`, `agy`).

## First implementation boundary

Feature 001 is deliberately limited to one ordinary text-layer PDF, page-aware
extraction, deterministic Obsidian scaffolding, indexed retrieval, and verified
atomic-memory synchronization. OCR, advanced layout reconstruction, automatic
reading agents, and Kanban automation follow after this slice is verified.

## Alternatives rejected

- **Query-time filesystem scan:** scales with vault size, repeats PDF parsing, and
  loses trust/namespace boundaries.
- **Make agent-memory canonical:** weakens Obsidian ownership and rebuildability.
- **Add another vector store:** duplicates the sibling engine.
- **Start with a watcher or full orchestrator:** adds reconciliation complexity
  before explicit ingestion and retrieval are proven.
- **Global content-only deduplication:** loses provenance when passages repeat.

## Consequences

### Positive

- Query work is independent of vault size.
- The retrieval database can be deleted and rebuilt.
- Source citations survive chunking and re-indexing.
- Claude, Codex, AGY, and future workers share one contract.
- Human review remains visible in Obsidian.

### Negative

- The first slice requires a small compatibility change in `agent-memory`.
- Corpus and index synchronization must be observable and retryable.
- SQLite is suitable for a demo but not the final scaling target.
- Difficult PDFs may be blocked until layout/OCR support is added.

## Reconsider when

Revisit this ADR if the system needs multi-user access control, document-block
relational queries, multimodal figure retrieval, or a production-scale hosted
index.

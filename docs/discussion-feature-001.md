# Feature 001 Architecture Council Log

**Question:** What is the smallest demoable implementation for an Obsidian-first
second brain that uses `agent-memory` for indexed retrieval rather than scanning
all Markdown/PDF files at question time?

**Participants:** Claude architecture reviewer, Codex architecture reviewer,
AGY/agentic-OS architecture reviewer, Hermes supervisor

## Shared proposal

```text
PDF → immutable source → page-aware corpus → agent-memory index
                         ↓
              Obsidian literature-note draft
                         ↓ human verification
              verified atomic note → brain index

Question → agent-memory recall → cited chunks
          (no PDF/Markdown traversal)
```

The council agreed to start with one explicitly named, ordinary text-layer PDF.
The first slice proves source identity, page provenance, deterministic note
creation, index-backed retrieval, idempotent reruns, and the human promotion
gate. OCR, advanced layout repair, autonomous reading, Kanban automation, and
full answer synthesis are deferred.

## Claude perspective

Claude recommended a narrow vertical slice: ingest one text-layer arXiv paper,
index it under `paper-corpus`, answer one cited retrieval question, and create
one unreviewed literature-note draft. Claude emphasized making the real
`agent-memory` contract an early integration risk rather than building a large
pipeline on assumptions. It rejected recursive file search, a second vector
store, and building the Kanban UI before the ingestion/retrieval loop is proven.

Key proposed controls:

- Page-aware extraction and citation locators
- No filesystem access in the query path
- Deterministic, idempotent note writes
- `promotion_status: blocked` for the first slice
- Tests that forbid opening corpus/source files during query

## Codex perspective

Codex inspected the sibling repository and identified blocking integration gaps:

- Current ingestion deduplication is globally keyed by content hash.
- `/remember` has no external idempotency key or upsert contract.
- Current PDF extraction concatenates pages and loses page provenance.
- `pypdf` is lazily imported but not an explicit project dependency.
- SQLite recall is linear over stored memories; acceptable for the demo, not the
  scale target.

Codex recommended a keyed `PUT /v1/memories/{external_id}` contract and a unique
`(user_id, namespace, external_id)` constraint. It also recommended retaining
source identity in the external ID so identical text in two sources keeps both
citations. The proposed first slice excludes OCR, layout models, automatic
claims, watchers, and a new vector store.

## AGY perspective

AGY recommended treating agents as proposal-producing workers behind explicit
handoffs:

- Ingestion worker: extraction, hashes, evidence, warnings
- Reading worker: candidate claims and summaries
- Reviewer worker: entailment and citation checks
- Human owner: final approval and promotion
- AGY: orchestration, state, retries, audit, and permissions

AGY emphasized that worker identity should be metadata rather than separate
provider-specific code paths. It recommended rejecting unverified atomic notes,
keeping an append-only audit trail, and allowing agents to abstain when evidence
is insufficient.

## Reconciliation

All three perspectives agreed on:

1. Obsidian and original sources remain canonical.
2. `agent-memory` is a rebuildable retrieval projection.
3. Query-time retrieval must use the index exclusively.
4. Source/page provenance is mandatory.
5. Generated claims must not enter `brain` automatically.
6. Idempotency and approved-note protection are acceptance criteria.
7. The first implementation must be a vertical slice, not a full platform.

The main difference was scope emphasis:

- Claude favored proving the smallest end-to-end demo quickly.
- Codex emphasized the required sibling-repository API changes.
- AGY emphasized long-term worker boundaries and approval state.

The merged decision is to implement the smallest demo while including the
minimum `agent-memory` compatibility work needed to make idempotency and
provenance real rather than aspirational.

## Implementation decision

Feature 001 will be implemented in this order:

1. Add source-scoped keyed upsert and metadata round-trip support to
   `agent-memory`.
2. Add `second-brain` source registration, page-aware extraction, corpus
   artifacts, and deterministic Obsidian scaffolding.
3. Add an index-backed query command with no source-file traversal.
4. Add verified-only atomic-note synchronization into `brain`.
5. Add end-to-end tests and a runnable demo fixture.

## Verification contract

A separate verification worker must confirm:

- PRD requirements are implemented, not merely documented.
- Tests cover idempotency, provenance, approved-note protection, namespace
  isolation, and no-filesystem-scan behavior.
- The exact CI commands pass.
- The demo can be run from a clean checkout with SQLite and no external LLM key.

## Verification follow-up: atomic-note provenance

Verified atomic memories must declare a non-empty provenance classification of
`user`, `source`, or `derived` before they may enter `brain`. The synchronization
adapter forwards that classification as index metadata. This makes promotion
auditable without expanding the Feature 001 scope or changing its PRD.

## Worker outputs

- Claude memo: architecture and smallest useful user experience
- Codex memo: API contract, repository gaps, and test matrix
- AGY memo: worker boundaries, approval gates, and auditability
- Final artifacts: `docs/prd-001-indexed-obsidian-second-brain.md`,
  `docs/adr-001-obsidian-canonical-agent-memory-derived.md`, and this log

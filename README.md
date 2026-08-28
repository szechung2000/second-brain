# second-brain

A provenance-first second-brain workflow for technical books, arXiv papers, and
agent-assisted Obsidian knowledge management.

This repository is the workflow and ingestion layer around the
[`agent-memory`](https://github.com/szechung2000/agent-memory) retrieval engine.
It keeps original sources, extracted evidence, curated Obsidian notes, and
approved durable memories distinct.

## Planned capabilities

- Kanban workflow for source ingestion and note approval
- Obsidian literature-note templates
- Technical PDF extraction with page, section, equation, table, and figure provenance
- Claude/Codex/AGY-assisted drafting with human approval gates
- Promotion of reviewed atomic knowledge into `agent-memory`

See the open pull requests for the initial design specifications.

## Feature 001 offline demo

`sb` registers one explicitly named text-layer PDF, writes immutable source and
versioned corpus artifacts into an Obsidian vault, then sends page-aware
evidence to the sibling `agent-memory` service. Start that service with SQLite:

```bash
cd /path/to/agent-memory
AM_DATABASE_URL=sqlite:///./agent_memory.db uv run uvicorn agent_memory.api.main:app
```

Then, from this repository:

```bash
uv sync
sb ingest sources/paper.pdf --vault ./vault --actor human --json
sb query "What assumptions does the method make?" --scope paper-corpus --k 5 --json
sb sync-atomic vault/Atomic/claim.md --vault ./vault --actor human --json
```

Only notes with `type: atomic-memory` and `status: verified` can be synchronized
to the `brain` namespace. Query only calls the memory index; it does not scan
the vault, Markdown notes, or PDFs.

Run the local checks with `uv run ruff check .` and `uv run pytest -q`.

"""The ``sb`` command for the Feature 001 offline demo."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from second_brain.ingest import ingest_pdf
from second_brain.memory import AgentMemoryAdapter
from second_brain.query import query
from second_brain.status import source_status
from second_brain.sync import sync_atomic_note


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sb")
    subparsers = parser.add_subparsers(dest="command", required=True)
    ingest = subparsers.add_parser("ingest")
    ingest.add_argument("pdf", type=Path)
    ingest.add_argument("--vault", type=Path, required=True)
    ingest.add_argument("--actor", choices=["human", "claude", "codex", "agy"], required=True)
    ingest.add_argument("--memory-url", default=_memory_url())
    ingest.add_argument("--json", action="store_true")
    status = subparsers.add_parser("status")
    status.add_argument("source_id")
    status.add_argument("--vault", type=Path, required=True)
    status.add_argument("--json", action="store_true")
    recall = subparsers.add_parser("query")
    recall.add_argument("text")
    recall.add_argument("--scope", action="append")
    recall.add_argument("--k", type=int, default=5)
    recall.add_argument("--memory-url", default=_memory_url())
    recall.add_argument("--json", action="store_true")
    sync = subparsers.add_parser("sync-atomic")
    sync.add_argument("note", type=Path)
    sync.add_argument("--vault", type=Path, required=True)
    sync.add_argument("--actor", choices=["human", "claude", "codex", "agy"], required=True)
    sync.add_argument("--memory-url", default=_memory_url())
    sync.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "ingest":
            output = ingest_pdf(
                args.pdf,
                vault=args.vault,
                actor=args.actor,
                memory=AgentMemoryAdapter(args.memory_url),
            ).as_dict()
            return _emit(output, args.json, failed=output["status"] == "blocked")
        if args.command == "status":
            return _emit(source_status(args.source_id, vault=args.vault), args.json)
        if args.command == "query":
            output = query(
                args.text,
                memory=AgentMemoryAdapter(args.memory_url),
                scopes=args.scope or ["paper-corpus"],
                k=args.k,
            )
            return _emit(output, args.json)
        output = sync_atomic_note(
            args.note,
            vault=args.vault,
            actor=args.actor,
            memory=AgentMemoryAdapter(args.memory_url),
        ).as_dict()
        return _emit(output, args.json)
    except (FileNotFoundError, ValueError, OSError) as error:
        return _emit({"error": str(error), "status": "error"}, args.json, failed=True)


def _memory_url() -> str:
    return os.environ.get("SB_MEMORY_URL", "http://127.0.0.1:8000")


def _emit(value: dict | list[dict], as_json: bool, *, failed: bool = False) -> int:
    if as_json:
        print(json.dumps(value, sort_keys=True))
    else:
        print(json.dumps(value, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

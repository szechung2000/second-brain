import second_brain.cli as cli


class Result:
    def __init__(self, payload):
        self.payload = payload

    def as_dict(self):
        return self.payload


def test_cli_emits_stable_json_and_nonzero_for_blocked_ingest(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(
        cli,
        "ingest_pdf",
        lambda *args, **kwargs: Result({"z_detail": "no text", "status": "blocked"}),
    )

    exit_code = cli.main(
        ["ingest", "empty.pdf", "--vault", str(tmp_path), "--actor", "human", "--json"]
    )

    assert exit_code == 1
    assert capsys.readouterr().out == '{"status": "blocked", "z_detail": "no text"}\n'


def test_cli_emits_stable_json_and_nonzero_for_operational_errors(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(
        cli,
        "ingest_pdf",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("source collision")),
    )

    exit_code = cli.main(
        ["ingest", "paper.pdf", "--vault", str(tmp_path), "--actor", "human", "--json"]
    )

    assert exit_code == 1
    assert capsys.readouterr().out == '{"error": "source collision", "status": "error"}\n'


def test_cli_successful_ingest_exits_zero_with_stable_json(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(
        cli,
        "ingest_pdf",
        lambda *args, **kwargs: Result({"z_path": "vault/run.json", "status": "extracted"}),
    )

    exit_code = cli.main(
        [
            "ingest",
            "paper.pdf",
            "--vault",
            str(tmp_path),
            "--actor",
            "human",
            "--memory-url",
            "http://memory.test",
            "--json",
        ]
    )

    assert exit_code == 0
    assert capsys.readouterr().out == '{"status": "extracted", "z_path": "vault/run.json"}\n'


def test_cli_status_exits_zero_with_stable_json(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(
        cli,
        "source_status",
        lambda *args, **kwargs: {"z_warning": [], "status": "extracted"},
    )

    exit_code = cli.main(["status", "sha256:paper", "--vault", str(tmp_path), "--json"])

    assert exit_code == 0
    assert capsys.readouterr().out == '{"status": "extracted", "z_warning": []}\n'


def test_cli_query_preserves_repeated_scopes_and_default_scope(monkeypatch, capsys):
    calls = []

    def fake_query(text, *, memory, scopes, k):
        calls.append((text, memory.base_url, scopes, k))
        return [{"z_source": "sha256:paper", "locator": "p. 1"}]

    monkeypatch.setattr(cli, "query", fake_query)

    repeated_exit_code = cli.main(
        [
            "query",
            "what changed?",
            "--scope",
            "brain",
            "--scope",
            "paper-corpus",
            "--k",
            "2",
            "--memory-url",
            "http://memory.test",
            "--json",
        ]
    )
    repeated_output = capsys.readouterr().out
    default_exit_code = cli.main(["query", "what changed?", "--json"])
    default_output = capsys.readouterr().out

    assert repeated_exit_code == default_exit_code == 0
    assert repeated_output == '[{"locator": "p. 1", "z_source": "sha256:paper"}]\n'
    assert default_output == '[{"locator": "p. 1", "z_source": "sha256:paper"}]\n'
    assert calls == [
        ("what changed?", "http://memory.test", ["brain", "paper-corpus"], 2),
        ("what changed?", "http://127.0.0.1:8000", ["paper-corpus"], 5),
    ]


def test_cli_sync_atomic_exits_zero_with_stable_json(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(
        cli,
        "sync_atomic_note",
        lambda *args, **kwargs: Result({"status": "synced", "z_memory": "memory-1"}),
    )

    exit_code = cli.main(
        [
            "sync-atomic",
            str(tmp_path / "Atomic" / "claim.md"),
            "--vault",
            str(tmp_path),
            "--actor",
            "codex",
            "--json",
        ]
    )

    assert exit_code == 0
    assert capsys.readouterr().out == '{"status": "synced", "z_memory": "memory-1"}\n'

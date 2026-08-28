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

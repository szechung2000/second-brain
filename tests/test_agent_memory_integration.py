"""Feature 001 paper-corpus path through the real sibling memory service."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_real_pdf_ingest_and_cli_query_use_agent_memory_without_file_scans(tmp_path):
    am_repo = Path(__file__).resolve().parents[2] / "am-repo"
    script = r'''
import builtins
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit

from fastapi.testclient import TestClient

sys.path.insert(0, os.environ["SECOND_BRAIN_SRC"])

from agent_memory.api.main import app
import second_brain.cli as cli
import second_brain.memory as second_brain_memory
from second_brain.ingest import ingest_pdf


class ClientHTTPResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


def text_layer_pdf(text):
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        ),
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    data = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(data))
        data.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    startxref = len(data)
    data.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    data.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
    data.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{startxref}\n%%EOF\n".encode()
    )
    return bytes(data)


work = Path(os.environ["INTEGRATION_WORK"])
pdf = work / "sample.pdf"
pdf.write_bytes(text_layer_pdf("The bounded input theorem supports stable retrieval."))
vault = work / "vault"
os.environ["AM_DATABASE_URL"] = f"sqlite:///{work / 'agent-memory.db'}"
from agent_memory.core.config import get_settings
get_settings.cache_clear()

with TestClient(app) as client:
    def testclient_urlopen(request, timeout):
        response = client.request(
            request.get_method(),
            urlsplit(request.full_url).path,
            content=request.data,
            headers=dict(request.header_items()),
        )
        if response.is_error:
            raise HTTPError(
                request.full_url,
                response.status_code,
                response.text,
                response.headers,
                None,
            )
        return ClientHTTPResponse(response.content)

    second_brain_memory.urlopen = testclient_urlopen
    result = ingest_pdf(
        pdf,
        vault=vault,
        actor="human",
        memory=second_brain_memory.AgentMemoryAdapter("http://testserver"),
    )
    assert result.status == "extracted"
    assert result.indexed_chunks == 1

    def fail_file_scan(*args, **kwargs):
        raise AssertionError("query must not scan Markdown or PDF files")

    builtins.open = fail_file_scan
    Path.open = fail_file_scan
    exit_code = cli.main(
        [
            "query",
            "bounded input theorem",
            "--scope",
            "paper-corpus",
            "--memory-url",
            "http://testserver",
            "--json",
        ]
    )
    assert exit_code == 0
'''
    harness = """
import contextlib
import io
import runpy
import sys

buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    runpy.run_path(sys.argv[1], run_name="__main__")
payload = buffer.getvalue()
assert '\"locator\": \"p. 1\"' in payload, payload
assert '\"source_id\": \"sha256:' in payload, payload
"""
    script_path = tmp_path / "integration.py"
    harness_path = tmp_path / "harness.py"
    script_path.write_text(script)
    harness_path.write_text(harness)
    completed = subprocess.run(
        ["uv", "run", "--project", str(am_repo), "python", str(harness_path), str(script_path)],
        check=False,
        capture_output=True,
        env={
            **os.environ,
            "INTEGRATION_WORK": str(tmp_path),
            "SECOND_BRAIN_SRC": str(Path(__file__).resolve().parents[1] / "src"),
        },
        text=True,
    )

    assert completed.returncode == 0, completed.stderr

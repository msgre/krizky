"""Tests for krizky.fetch module."""

from __future__ import annotations

import stat
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from krizky.fetch import FetchError, TransformError, fetch_doc, fetch_sheet, run_transform


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_response(body: bytes) -> MagicMock:
    """Return a MagicMock that behaves like a urllib context-manager response."""
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.read.return_value = body
    return mock_response


def _make_script(tmp_path: Path, content: str, name: str = "transform.sh") -> Path:
    """Write a bash script to *tmp_path* and make it executable."""
    script = tmp_path / name
    script.write_text(textwrap.dedent(content), encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return script


# ---------------------------------------------------------------------------
# test_fetch_sheet_basic
# ---------------------------------------------------------------------------

def test_fetch_sheet_basic(tmp_path: Path) -> None:
    """fetch_sheet downloads CSV content and writes it to the output file."""
    csv_body = b"col1,col2\nval1,val2\n"
    mock_response = _make_mock_response(csv_body)

    output_path = tmp_path / "out" / "data.csv"

    with patch("urllib.request.urlopen", return_value=mock_response):
        fetch_sheet("SHEET_ID", "0", output_path)

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == "col1,col2\nval1,val2\n"


# ---------------------------------------------------------------------------
# test_fetch_sheet_skip_rows
# ---------------------------------------------------------------------------

def test_fetch_sheet_skip_rows(tmp_path: Path) -> None:
    """fetch_sheet with skip_rows=2 drops the first 2 lines of CSV content."""
    csv_body = b"header1\nheader2\ncol1,col2\nval1,val2\n"
    mock_response = _make_mock_response(csv_body)

    output_path = tmp_path / "data.csv"

    with patch("urllib.request.urlopen", return_value=mock_response):
        fetch_sheet("SHEET_ID", "0", output_path, skip_rows=2)

    content = output_path.read_text(encoding="utf-8")
    assert content == "col1,col2\nval1,val2\n"
    assert "header1" not in content
    assert "header2" not in content


# ---------------------------------------------------------------------------
# test_fetch_doc_basic
# ---------------------------------------------------------------------------

def test_fetch_doc_basic(tmp_path: Path) -> None:
    """fetch_doc downloads binary DOCX content and writes it to the output file."""
    docx_body = b"\x50\x4b\x03\x04fake_docx_binary_content"
    mock_response = _make_mock_response(docx_body)

    output_path = tmp_path / "out" / "doc.docx"

    with patch("urllib.request.urlopen", return_value=mock_response):
        fetch_doc("DOC_ID", output_path)

    assert output_path.exists()
    assert output_path.read_bytes() == docx_body


# ---------------------------------------------------------------------------
# test_run_transform_success
# ---------------------------------------------------------------------------

def test_run_transform_success(tmp_path: Path) -> None:
    """run_transform does not raise when the script exits with code 0."""
    script = _make_script(
        tmp_path,
        """\
        #!/usr/bin/env bash
        exit 0
        """,
    )
    db_path = tmp_path / "data.db"
    source_file = tmp_path / "source.csv"
    source_file.write_text("col1\nval1\n", encoding="utf-8")

    # Should not raise
    run_transform(script, source_file, db_path, "test_table")


# ---------------------------------------------------------------------------
# test_run_transform_failure
# ---------------------------------------------------------------------------

def test_run_transform_failure(tmp_path: Path) -> None:
    """run_transform raises TransformError when the script exits with code 1."""
    script = _make_script(
        tmp_path,
        """\
        #!/usr/bin/env bash
        exit 1
        """,
    )
    db_path = tmp_path / "data.db"
    source_file = tmp_path / "source.csv"
    source_file.write_text("col1\nval1\n", encoding="utf-8")

    with pytest.raises(TransformError, match="exited with code 1"):
        run_transform(script, source_file, db_path, "test_table")


# ---------------------------------------------------------------------------
# test_fetch_sheet_http_error
# ---------------------------------------------------------------------------

def test_fetch_sheet_http_error(tmp_path: Path) -> None:
    """fetch_sheet raises FetchError on HTTP errors."""
    import urllib.error

    output_path = tmp_path / "data.csv"

    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.HTTPError(url=None, code=403, msg="Forbidden", hdrs=None, fp=None),
    ):
        with pytest.raises(FetchError, match="403"):
            fetch_sheet("SHEET_ID", "0", output_path)


# ---------------------------------------------------------------------------
# test_fetch_doc_http_error
# ---------------------------------------------------------------------------

def test_fetch_doc_http_error(tmp_path: Path) -> None:
    """fetch_doc raises FetchError on HTTP errors."""
    import urllib.error

    output_path = tmp_path / "doc.docx"

    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.HTTPError(url=None, code=404, msg="Not Found", hdrs=None, fp=None),
    ):
        with pytest.raises(FetchError, match="404"):
            fetch_doc("DOC_ID", output_path)

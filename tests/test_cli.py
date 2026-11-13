"""Tests for error reporting in `krizky build site`."""

import sqlite3
import sys
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from krizky.cli import _find_plugin_in_traceback, _format_error_line, cli

PLUGIN_SRC = """
import pluggy

hookimpl = pluggy.HookimplMarker("krizky")


class FocalPointsError(Exception):
    pass


class Plugin:
    @hookimpl
    def prepare_jinja2_environment(self, env, config, config_dir=None):
        raise FocalPointsError("bad focal point")


plugin = Plugin()
"""


def _project(tmp_path: Path, with_db: bool = True) -> Path:
    (tmp_path / "sources").mkdir()
    if with_db:
        conn = sqlite3.connect(str(tmp_path / "sources" / "data.db"))
        conn.execute("CREATE TABLE data (nazev TEXT)")
        conn.execute("INSERT INTO data VALUES ('a')")
        conn.commit()
        conn.close()
    (tmp_path / "transform.sh").write_text("#!/bin/bash\n")
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "index.html").write_text("hi")
    (tmp_path / "plugins").mkdir()
    (tmp_path / "plugins" / "boom.py").write_text(PLUGIN_SRC)
    config = {
        "sources": {
            "output": "./sources",
            "database": "data.db",
            "tables": {"data": {"main": True, "transform": "./transform.sh"}},
        },
        "site": {
            "title": "T",
            "output": "./output",
            "templates": "./templates",
            "pages": {"home": {"path": "/index.html", "template": "index.html"}},
        },
    }
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump(config))
    return cfg


@pytest.fixture(autouse=True)
def _cleanup_boom():
    yield
    sys.modules.pop("boom", None)


def _run(cfg: Path, *args: str):
    return CliRunner().invoke(cli, ["--config", str(cfg), "build", "site", *args])


def test_plugin_error_one_line(tmp_path):
    result = _run(_project(tmp_path))
    assert result.exit_code == 1
    assert "ERROR: boom: FocalPointsError: bad focal point" in result.output
    assert "--verbose" in result.output
    assert "Traceback" not in result.output


def test_plugin_error_verbose_traceback(tmp_path):
    result = _run(_project(tmp_path), "-v")
    assert result.exit_code == 1
    assert "ERROR: boom: FocalPointsError: bad focal point" in result.output
    assert "Traceback" in result.output


def test_error_outside_plugin(tmp_path, monkeypatch):
    cfg = _project(tmp_path)

    def fake(*args, **kwargs):
        raise RuntimeError("x")

    monkeypatch.setattr("krizky.site.build_site", fake)
    result = _run(cfg)
    assert result.exit_code == 1
    assert "ERROR: RuntimeError: x" in result.output
    assert "boom" not in result.output


def test_site_error_unchanged(tmp_path):
    result = _run(_project(tmp_path, with_db=False))
    assert result.exit_code == 1
    assert "ERROR: Database not found" in result.output
    assert "--verbose" not in result.output
    assert "Traceback" not in result.output


def test_help_mentions_traceback():
    result = CliRunner().invoke(cli, ["build", "site", "--help"])
    assert "traceback" in result.output


def test_format_error_line():
    assert _format_error_line(ValueError("m"), "p") == "ERROR: p: ValueError: m"
    assert _format_error_line(ValueError("m"), None) == "ERROR: ValueError: m"


def test_find_plugin_in_traceback():
    with pytest.raises(ValueError, match="x") as info:
        raise ValueError("x")
    tb = info.value.__traceback__
    assert _find_plugin_in_traceback(tb, {"nope"}) is None
    assert _find_plugin_in_traceback(tb, {"tests"}) == "tests"
    assert _find_plugin_in_traceback(None, {"tests"}) is None

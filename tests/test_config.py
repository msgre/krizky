"""Tests for krizky.config module."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from krizky.config import ConfigError, load_config, validate_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_yaml(tmp_path: Path, content: str, filename: str = "config.yaml") -> Path:
    """Write *content* to a YAML file inside *tmp_path* and return its path."""
    p = tmp_path / filename
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def make_script(tmp_path: Path) -> Path:
    """Create a minimal executable script in tmp_path and return its path."""
    script = tmp_path / "dummy.sh"
    script.write_text("#!/bin/sh\n")
    script.chmod(0o755)
    return script


def minimal_valid_config(script_path: Path) -> dict:
    """Return a minimal configuration dict that passes validate_config()."""
    return {
        "sources": {
            "tables": {
                "data": {"main": True, "transform": str(script_path)},
            },
            "docs": {},
        },
        "site": {
            "base_url": "https://example.com",
        },
    }


# ---------------------------------------------------------------------------
# test_load_config_basic
# ---------------------------------------------------------------------------

def test_load_config_basic(tmp_path: Path) -> None:
    """load_config returns a dict for a valid YAML file."""
    p = write_yaml(
        tmp_path,
        """\
        sources:
            output: ./sources
            tables:
                data:
                    main: true
        site:
            base_url: https://example.com
        """,
    )
    config = load_config(str(p))
    assert isinstance(config, dict)
    assert "sources" in config
    assert "site" in config
    assert config["site"]["base_url"] == "https://example.com"


# ---------------------------------------------------------------------------
# test_env_substitution
# ---------------------------------------------------------------------------

def test_env_substitution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Values starting with '$' are replaced with the env variable value."""
    monkeypatch.setenv("MY_VAR", "hello_world")
    p = write_yaml(
        tmp_path,
        """\
        sources:
            tables:
                data:
                    main: true
        site:
            base_url: $MY_VAR
        """,
    )
    config = load_config(str(p))
    assert config["site"]["base_url"] == "hello_world"


# ---------------------------------------------------------------------------
# test_env_substitution_missing
# ---------------------------------------------------------------------------

def test_env_substitution_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing env variable referenced as '$VAR' raises ConfigError."""
    # Ensure the variable is definitely not set
    monkeypatch.delenv("DEFINITELY_MISSING_VAR_XYZ", raising=False)
    p = write_yaml(
        tmp_path,
        """\
        sources:
            tables:
                data:
                    main: true
        site:
            secret: $DEFINITELY_MISSING_VAR_XYZ
        """,
    )
    with pytest.raises(ConfigError, match="DEFINITELY_MISSING_VAR_XYZ"):
        load_config(str(p))


# ---------------------------------------------------------------------------
# test_validate_main_true_missing
# ---------------------------------------------------------------------------

def test_validate_main_true_missing() -> None:
    """validate_config raises ConfigError when no table has main: true."""
    config = {
        "sources": {
            "tables": {
                "data": {"id": "abc"},
                "snippets": {"id": "def"},
            },
        },
        "site": {},
    }
    with pytest.raises(ConfigError, match="main: true"):
        validate_config(config)


# ---------------------------------------------------------------------------
# test_validate_main_true_duplicate
# ---------------------------------------------------------------------------

def test_validate_main_true_duplicate() -> None:
    """validate_config raises ConfigError when more than one table has main: true."""
    config = {
        "sources": {
            "tables": {
                "data": {"main": True},
                "other": {"main": True},
            },
        },
        "site": {},
    }
    with pytest.raises(ConfigError, match="main: true"):
        validate_config(config)


# ---------------------------------------------------------------------------
# test_validate_docs_missing_output
# ---------------------------------------------------------------------------

def test_validate_docs_missing_output(tmp_path: Path) -> None:
    """validate_config raises ConfigError when a docs entry lacks 'output'."""
    script = make_script(tmp_path)
    config = {
        "sources": {
            "tables": {
                "data": {"main": True, "transform": str(script)},
            },
            "docs": {
                "uvod": {
                    "id": "some_id",
                    "transform": str(script),
                    # 'output' is intentionally missing
                },
            },
        },
        "site": {},
    }
    with pytest.raises(ConfigError, match="output"):
        validate_config(config)


# ---------------------------------------------------------------------------
# Additional edge-case tests
# ---------------------------------------------------------------------------

def test_load_config_file_not_found(tmp_path: Path) -> None:
    """load_config raises ConfigError for a nonexistent file."""
    with pytest.raises(ConfigError, match="not found"):
        load_config(str(tmp_path / "nonexistent.yaml"))


def test_env_substitution_nested(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ENV substitution works recursively in nested dicts and lists."""
    monkeypatch.setenv("NESTED_VAR", "nested_value")
    p = write_yaml(
        tmp_path,
        """\
        sources:
            tables:
                data:
                    main: true
            photos:
                formats:
                    - format: jpg
                      key: $NESTED_VAR
        site: {}
        """,
    )
    config = load_config(str(p))
    assert config["sources"]["photos"]["formats"][0]["key"] == "nested_value"


def test_validate_config_missing_sources_section() -> None:
    """validate_config raises ConfigError when 'sources' section is absent."""
    with pytest.raises(ConfigError, match="sources"):
        validate_config({"site": {}})


def test_validate_config_missing_site_section() -> None:
    """validate_config raises ConfigError when 'site' section is absent."""
    config = {
        "sources": {
            "tables": {"data": {"main": True}},
        },
    }
    with pytest.raises(ConfigError, match="site"):
        validate_config(config)


def test_validate_docs_missing_transform(tmp_path: Path) -> None:
    """validate_config raises ConfigError when a docs entry lacks 'transform'."""
    script = make_script(tmp_path)
    config = {
        "sources": {
            "tables": {"data": {"main": True, "transform": str(script)}},
            "docs": {
                "uvod": {
                    "id": "some_id",
                    "output": "uvod.md",
                    # 'transform' is intentionally missing
                },
            },
        },
        "site": {},
    }
    with pytest.raises(ConfigError, match="transform"):
        validate_config(config)


def test_validate_tables_missing_transform() -> None:
    """validate_config raises ConfigError when a table lacks 'transform'."""
    config = {
        "sources": {
            "tables": {
                "data": {"main": True},  # 'transform' is intentionally missing
            },
        },
        "site": {},
    }
    with pytest.raises(ConfigError, match="transform"):
        validate_config(config)

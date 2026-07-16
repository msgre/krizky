"""Tests for krizky.query — QueryRunner and _render_parameterized."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from krizky.query import QueryRunner, _render_parameterized
from krizky.site import build_site


# ---------------------------------------------------------------------------
# _render_parameterized
# ---------------------------------------------------------------------------

def test_render_parameterized_basic():
    """Each {{ param }} becomes ? and the value is collected in order."""
    sql, values = _render_parameterized(
        "SELECT * FROM t WHERE lat > {{ min_lat }} AND lat < {{ max_lat }}",
        {"min_lat": 49.0, "max_lat": 50.0},
    )
    assert sql == "SELECT * FROM t WHERE lat > ? AND lat < ?"
    assert values == [49.0, 50.0]


def test_render_parameterized_same_param_twice():
    """Same param referenced twice → two ? placeholders, value collected twice."""
    sql, values = _render_parameterized(
        "SELECT * FROM t WHERE a = {{ x }} AND b = {{ x }}",
        {"x": 42},
    )
    assert sql == "SELECT * FROM t WHERE a = ? AND b = ?"
    assert values == [42, 42]


def test_render_parameterized_constant_default():
    """Missing param with |default(N) renders as literal, not a placeholder."""
    sql, values = _render_parameterized(
        "LIMIT {{ limit|default(10) }}",
        {},
    )
    assert sql == "LIMIT 10"
    assert values == []


def test_render_parameterized_mixed():
    """Mix of bound param and constant default."""
    sql, values = _render_parameterized(
        "WHERE lat = {{ lat }} LIMIT {{ limit|default(5) }}",
        {"lat": 49.5},
    )
    assert sql == "WHERE lat = ? LIMIT 5"
    assert values == [49.5]


def test_render_parameterized_sql_injection():
    """String param containing SQL injection payload is collected as value, not injected."""
    payload = "'; DROP TABLE mista; --"
    sql, values = _render_parameterized(
        "SELECT * FROM t WHERE name = {{ name }}",
        {"name": payload},
    )
    assert sql == "SELECT * FROM t WHERE name = ?"
    assert values == [payload]
    assert "DROP" not in sql


def test_render_parameterized_none_value():
    """None param becomes ? with None value (SQLite will use NULL)."""
    sql, values = _render_parameterized("WHERE x = {{ x }}", {"x": None})
    assert sql == "WHERE x = ?"
    assert values == [None]


# ---------------------------------------------------------------------------
# QueryRunner — unit tests with real SQLite
# ---------------------------------------------------------------------------

def _make_conn(records: list[dict], table: str = "items") -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    if records:
        cols = list(records[0].keys())
        col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
        conn.execute(f'CREATE TABLE "{table}" ({col_defs})')
        placeholders = ", ".join("?" for _ in cols)
        for rec in records:
            conn.execute(
                f'INSERT INTO "{table}" VALUES ({placeholders})',
                [rec.get(c) for c in cols],
            )
        conn.commit()
    return conn


def test_query_basic():
    """QueryRunner executes SQL and returns matching records."""
    conn = _make_conn([
        {"slug": "a", "val": "10"},
        {"slug": "b", "val": "20"},
        {"slug": "c", "val": "30"},
    ])
    cfg = {
        "big": {"sql": 'SELECT * FROM items WHERE CAST(val AS INTEGER) > {{ threshold }}'},
    }
    runner = QueryRunner(conn, cfg)
    result = runner("big", threshold=15)
    assert len(result) == 2
    assert result[0]["slug"] == "b"
    assert result[1]["slug"] == "c"


def test_query_returns_dicts():
    """Results are plain dicts, not sqlite3.Row objects."""
    conn = _make_conn([{"slug": "x", "val": "1"}])
    cfg = {"all": {"sql": "SELECT * FROM items"}}
    runner = QueryRunner(conn, cfg)
    result = runner("all")
    assert isinstance(result[0], dict)


def test_query_caching():
    """Second call with identical params returns cached result without re-executing."""
    conn = _make_conn([{"slug": "a", "val": "1"}])
    cfg = {"q": {"sql": "SELECT * FROM items WHERE val = {{ v }}"}}
    runner = QueryRunner(conn, cfg)

    first = runner("q", v="1")
    # Mutate the DB — cached result should still be returned
    conn.execute("DELETE FROM items")
    conn.commit()
    second = runner("q", v="1")

    assert first is second  # same list object from cache
    assert len(second) == 1


def test_query_cache_miss_on_different_params():
    """Different params produce separate cache entries."""
    conn = _make_conn([
        {"slug": "a", "val": "1"},
        {"slug": "b", "val": "2"},
    ])
    cfg = {"q": {"sql": "SELECT * FROM items WHERE val = {{ v }}"}}
    runner = QueryRunner(conn, cfg)

    r1 = runner("q", v="1")
    r2 = runner("q", v="2")

    assert len(r1) == 1 and r1[0]["slug"] == "a"
    assert len(r2) == 1 and r2[0]["slug"] == "b"


def test_query_unknown_name_returns_empty():
    """Unknown query name returns [] without raising."""
    conn = _make_conn([])
    runner = QueryRunner(conn, {})
    result = runner("nonexistent")
    assert result == []


def test_query_unknown_name_logs_warning(caplog):
    """Unknown query name emits a warning log."""
    import logging
    conn = _make_conn([])
    runner = QueryRunner(conn, {})
    with caplog.at_level(logging.WARNING, logger="krizky.query"):
        runner("nonexistent")
    assert "nonexistent" in caplog.text


def test_query_bad_sql_returns_empty():
    """Invalid SQL logs an error and returns [] without raising."""
    conn = _make_conn([{"slug": "a", "val": "1"}])
    cfg = {"broken": {"sql": "THIS IS NOT VALID SQL {{ x }}"}}
    runner = QueryRunner(conn, cfg)
    result = runner("broken", x=1)
    assert result == []


def test_query_bad_sql_logs_error(caplog):
    """Invalid SQL produces an error log entry."""
    import logging
    conn = _make_conn([{"slug": "a", "val": "1"}])
    cfg = {"broken": {"sql": "TOTALLY BROKEN {{ x }}"}}
    runner = QueryRunner(conn, cfg)
    with caplog.at_level(logging.ERROR, logger="krizky.query"):
        runner("broken", x=1)
    assert "broken" in caplog.text


# ---------------------------------------------------------------------------
# Integration: query() callable in Jinja2 template via build_site
# ---------------------------------------------------------------------------

def _make_db_file(db_path: Path, records: list[dict], table: str = "data") -> None:
    conn = sqlite3.connect(str(db_path))
    cols = list(records[0].keys())
    col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
    conn.execute(f'CREATE TABLE "{table}" ({col_defs})')
    placeholders = ", ".join("?" for _ in cols)
    for rec in records:
        conn.execute(
            f'INSERT INTO "{table}" VALUES ({placeholders})',
            [rec.get(c) for c in cols],
        )
    conn.commit()
    conn.close()


def test_query_in_template(tmp_path: Path):
    """query() is available in Jinja2 templates and returns correct data."""
    records = [
        {"slug": "a", "val": "10"},
        {"slug": "b", "val": "20"},
        {"slug": "c", "val": "30"},
    ]
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()
    _make_db_file(sources_dir / "data.db", records)

    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    # Template calls query() with a threshold and renders matching slugs
    (templates_dir / "page.html").write_text(
        "{% set res = query('big', threshold='15') %}"
        "{% for r in res %}{{ r.slug }}{% endfor %}",
        encoding="utf-8",
    )

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    config = {
        "sources": {
            "output": str(sources_dir),
            "database": "data.db",
            "tables": {"data": {"main": True}},
        },
        "site": {
            "title": "Test",
            "output": str(output_dir),
            "templates": str(templates_dir),
            "pages": {"all": {"path": "/all.html", "template": "page.html"}},
        },
        "queries": {
            "big": {
                "sql": "SELECT * FROM data WHERE CAST(val AS INTEGER) > {{ threshold }}",
            },
        },
    }

    build_site(config, config_dir=tmp_path)

    out = (output_dir / "all.html").read_text(encoding="utf-8")
    assert "b" in out
    assert "c" in out
    assert "a" not in out


def test_query_in_detail_template(tmp_path: Path):
    """query() called with record field value works on detail pages."""
    records = [
        {"slug": "main-a", "ref": "x"},
        {"slug": "main-b", "ref": "y"},
    ]
    related = [
        {"slug": "rel-x", "ref": "x"},
        {"slug": "rel-y", "ref": "y"},
        {"slug": "rel-z", "ref": "z"},
    ]
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()

    conn = sqlite3.connect(str(sources_dir / "data.db"))
    conn.row_factory = sqlite3.Row
    conn.execute('CREATE TABLE data (slug TEXT, ref TEXT)')
    for r in records:
        conn.execute('INSERT INTO data VALUES (?, ?)', [r["slug"], r["ref"]])
    conn.execute('CREATE TABLE related (slug TEXT, ref TEXT)')
    for r in related:
        conn.execute('INSERT INTO related VALUES (?, ?)', [r["slug"], r["ref"]])
    conn.commit()
    conn.close()

    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "detail.html").write_text(
        "{{ record.slug }}:"
        "{% set res = query('by_ref', ref=record.ref) %}"
        "{% for r in res %}{{ r.slug }}{% endfor %}",
        encoding="utf-8",
    )

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    config = {
        "sources": {
            "output": str(sources_dir),
            "database": "data.db",
            "tables": {"data": {"main": True}},
        },
        "site": {
            "title": "Test",
            "output": str(output_dir),
            "templates": str(templates_dir),
            "pages": {
                "detail": {
                    "detail": True,
                    "path": "/{{ record.slug }}.html",
                    "template": "detail.html",
                },
            },
        },
        "queries": {
            "by_ref": {
                "sql": "SELECT * FROM related WHERE ref = {{ ref }}",
            },
        },
    }

    build_site(config, config_dir=tmp_path)

    out_a = (output_dir / "main-a.html").read_text(encoding="utf-8")
    assert "main-a:rel-x" == out_a

    out_b = (output_dir / "main-b.html").read_text(encoding="utf-8")
    assert "main-b:rel-y" == out_b

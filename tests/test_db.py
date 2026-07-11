"""Tests for krizky.db — category and tag query functions."""

import json
import sqlite3
from pathlib import Path

import pytest

from krizky.db import (
    fetch_by_category,
    fetch_by_tag,
    fetch_distinct_categories,
    fetch_distinct_tags,
    fetch_records,
    parse_row,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _conn(tmp_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    conn.row_factory = sqlite3.Row
    return conn


def _make_table(conn: sqlite3.Connection, rows: list[dict], table: str = "data") -> None:
    cols = list(rows[0].keys())
    col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
    conn.execute(f'CREATE TABLE "{table}" ({col_defs})')
    ph = ", ".join("?" for _ in cols)
    for row in rows:
        conn.execute(f'INSERT INTO "{table}" VALUES ({ph})', [row.get(c) for c in cols])
    conn.commit()


# ---------------------------------------------------------------------------
# fetch_distinct_categories
# ---------------------------------------------------------------------------

def test_fetch_distinct_categories_basic(tmp_path: Path) -> None:
    conn = _conn(tmp_path)
    _make_table(conn, [
        {"typ": "kriz", "typ_slug": "kriz"},
        {"typ": "kriz", "typ_slug": "kriz"},
        {"typ": "socha", "typ_slug": "socha"},
    ])
    result = fetch_distinct_categories(conn, "data", "typ", "typ_slug")
    assert set(result) == {("kriz", "kriz"), ("socha", "socha")}


def test_fetch_distinct_categories_skips_null_and_empty(tmp_path: Path) -> None:
    conn = _conn(tmp_path)
    _make_table(conn, [
        {"typ": "kriz", "typ_slug": "kriz"},
        {"typ": None, "typ_slug": None},
        {"typ": "", "typ_slug": ""},
    ])
    result = fetch_distinct_categories(conn, "data", "typ", "typ_slug")
    assert result == [("kriz", "kriz")]


def test_fetch_distinct_categories_with_condition(tmp_path: Path) -> None:
    conn = _conn(tmp_path)
    _make_table(conn, [
        {"typ": "kriz", "typ_slug": "kriz", "stav": "ok"},
        {"typ": "socha", "typ_slug": "socha", "stav": "hidden"},
    ])
    result = fetch_distinct_categories(conn, "data", "typ", "typ_slug", condition="stav = 'ok'")
    assert result == [("kriz", "kriz")]


# ---------------------------------------------------------------------------
# fetch_distinct_tags
# ---------------------------------------------------------------------------

def test_fetch_distinct_tags_basic(tmp_path: Path) -> None:
    conn = _conn(tmp_path)
    _make_table(conn, [
        {
            "stitky": json.dumps(["priroda", "kamen"]),
            "stitky_slug": json.dumps({"priroda": "priroda", "kamen": "kamen"}),
        },
        {
            "stitky": json.dumps(["priroda"]),
            "stitky_slug": json.dumps({"priroda": "priroda"}),
        },
    ])
    result = fetch_distinct_tags(conn, "data", "stitky", "stitky_slug")
    assert set(result) == {("priroda", "priroda"), ("kamen", "kamen")}


def test_fetch_distinct_tags_with_condition(tmp_path: Path) -> None:
    conn = _conn(tmp_path)
    _make_table(conn, [
        {
            "stitky": json.dumps(["priroda"]),
            "stitky_slug": json.dumps({"priroda": "priroda"}),
            "stav": "ok",
        },
        {
            "stitky": json.dumps(["kamen"]),
            "stitky_slug": json.dumps({"kamen": "kamen"}),
            "stav": "hidden",
        },
    ])
    result = fetch_distinct_tags(conn, "data", "stitky", "stitky_slug", condition="stav = 'ok'")
    assert result == [("priroda", "priroda")]


# ---------------------------------------------------------------------------
# fetch_by_category
# ---------------------------------------------------------------------------

def test_fetch_by_category_basic(tmp_path: Path) -> None:
    conn = _conn(tmp_path)
    _make_table(conn, [
        {"slug": "a", "typ": "kriz"},
        {"slug": "b", "typ": "socha"},
        {"slug": "c", "typ": "kriz"},
    ])
    result = fetch_by_category(conn, "data", "rowid", "asc", "typ", "kriz")
    assert [r["slug"] for r in result] == ["a", "c"]


def test_fetch_by_category_with_condition(tmp_path: Path) -> None:
    conn = _conn(tmp_path)
    _make_table(conn, [
        {"slug": "a", "typ": "kriz", "stav": "ok"},
        {"slug": "b", "typ": "kriz", "stav": "hidden"},
    ])
    result = fetch_by_category(conn, "data", "rowid", "asc", "typ", "kriz", condition="stav = 'ok'")
    assert [r["slug"] for r in result] == ["a"]


# ---------------------------------------------------------------------------
# fetch_by_tag
# ---------------------------------------------------------------------------

def test_fetch_by_tag_basic(tmp_path: Path) -> None:
    conn = _conn(tmp_path)
    _make_table(conn, [
        {"slug": "a", "stitky": json.dumps(["priroda", "kamen"])},
        {"slug": "b", "stitky": json.dumps(["priroda"])},
        {"slug": "c", "stitky": json.dumps(["kamen"])},
    ])
    result = fetch_by_tag(conn, "data", "rowid", "asc", "stitky", "priroda")
    assert [r["slug"] for r in result] == ["a", "b"]


def test_fetch_by_tag_with_condition(tmp_path: Path) -> None:
    conn = _conn(tmp_path)
    _make_table(conn, [
        {"slug": "a", "stitky": json.dumps(["priroda"]), "stav": "ok"},
        {"slug": "b", "stitky": json.dumps(["priroda"]), "stav": "hidden"},
    ])
    result = fetch_by_tag(conn, "data", "rowid", "asc", "stitky", "priroda", condition="stav = 'ok'")
    assert [r["slug"] for r in result] == ["a"]


def test_parse_row_strips_whitespace(tmp_path: Path) -> None:
    conn = _conn(tmp_path)
    _make_table(conn, [{"slug": "  kríž\n\n", "nazev": "\t Valašské nebe "}])
    result = fetch_records(conn, "data")
    assert result[0]["slug"] == "kríž"
    assert result[0]["nazev"] == "Valašské nebe"


def test_parse_row_strips_before_json_parse(tmp_path: Path) -> None:
    conn = _conn(tmp_path)
    _make_table(conn, [{"tags": '  ["a", "b"]\n'}])
    result = fetch_records(conn, "data")
    assert result[0]["tags"] == ["a", "b"]

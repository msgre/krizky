"""Tests for JSON export alongside HTML generation."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from krizky.site import build_site


# ---------------------------------------------------------------------------
# Helpers (zkopírované z test_site.py)
# ---------------------------------------------------------------------------

def _make_db(db_path: Path, records: list[dict], table: str = "data") -> None:
    cols = list(records[0].keys())
    conn = sqlite3.connect(str(db_path))
    col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
    conn.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({col_defs})')
    placeholders = ", ".join("?" for _ in cols)
    for rec in records:
        conn.execute(f'INSERT INTO "{table}" VALUES ({placeholders})', [rec.get(c) for c in cols])
    conn.commit()
    conn.close()


def _setup(tmp_path: Path, records: list[dict], pages: dict) -> dict:
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()
    _make_db(sources_dir / "data.db", records)
    (tmp_path / "templates").mkdir(exist_ok=True)
    (tmp_path / "output").mkdir(exist_ok=True)
    (tmp_path / "templates" / "page.html").write_text("ok", encoding="utf-8")
    return {
        "sources": {
            "output": str(sources_dir),
            "database": "data.db",
            "tables": {"data": {"main": True}},
        },
        "site": {
            "title": "Test",
            "output": str(tmp_path / "output"),
            "templates": str(tmp_path / "templates"),
            "pages": pages,
        },
    }


# ---------------------------------------------------------------------------
# Jednoduché stránky
# ---------------------------------------------------------------------------

def test_simple_page_json_all_fields(tmp_path: Path) -> None:
    """simple page s json: fields: '*' exportuje všechny záznamy."""
    records = [{"slug": "a", "nazev": "První"}, {"slug": "b", "nazev": "Druhý"}]
    config = _setup(tmp_path, records, {
        "mista": {
            "path": "/mista.html",
            "template": "page.html",
            "json": {"fields": "*"},
        },
    })
    build_site(config, config_dir=tmp_path)

    out = json.loads((tmp_path / "output" / "jsons" / "mista.json").read_text(encoding="utf-8"))
    assert len(out) == 2
    assert out[0]["slug"] == "a"
    assert out[1]["nazev"] == "Druhý"


def test_simple_page_json_field_whitelist(tmp_path: Path) -> None:
    """fields: [...] omezí exportované atributy."""
    records = [{"slug": "a", "nazev": "První", "interni": "tajne"}]
    config = _setup(tmp_path, records, {
        "mista": {
            "path": "/mista.html",
            "template": "page.html",
            "json": {"fields": ["slug", "nazev"]},
        },
    })
    build_site(config, config_dir=tmp_path)

    out = json.loads((tmp_path / "output" / "jsons" / "mista.json").read_text(encoding="utf-8"))
    assert list(out[0].keys()) == ["slug", "nazev"]
    assert "interni" not in out[0]


def test_simple_page_json_exclude(tmp_path: Path) -> None:
    """exclude: [...] odstraní uvedená pole ze všech záznamů."""
    records = [{"slug": "a", "nazev": "První", "interni": "tajne"}]
    config = _setup(tmp_path, records, {
        "mista": {
            "path": "/mista.html",
            "template": "page.html",
            "json": {"fields": "*", "exclude": ["interni"]},
        },
    })
    build_site(config, config_dir=tmp_path)

    out = json.loads((tmp_path / "output" / "jsons" / "mista.json").read_text(encoding="utf-8"))
    assert "interni" not in out[0]
    assert "slug" in out[0]


def test_simple_page_json_pretty(tmp_path: Path) -> None:
    """pretty: true generuje odsazený JSON."""
    records = [{"slug": "a"}]
    config = _setup(tmp_path, records, {
        "mista": {
            "path": "/mista.html",
            "template": "page.html",
            "json": {"fields": "*", "pretty": True},
        },
    })
    build_site(config, config_dir=tmp_path)

    raw = (tmp_path / "output" / "jsons" / "mista.json").read_text(encoding="utf-8")
    assert "\n" in raw  # odsazený výstup


def test_simple_page_no_json_without_key(tmp_path: Path) -> None:
    """Bez json: klíče se JSON soubor negeneruje."""
    records = [{"slug": "a"}]
    config = _setup(tmp_path, records, {
        "mista": {"path": "/mista.html", "template": "page.html"},
    })
    build_site(config, config_dir=tmp_path)

    assert not (tmp_path / "output" / "jsons" / "mista.json").exists()


def test_simple_page_json_ignores_pagination(tmp_path: Path) -> None:
    """JSON exportuje všechny záznamy i při stránkování HTML."""
    records = [{"slug": str(i), "nazev": f"Item {i}"} for i in range(5)]
    config = _setup(tmp_path, records, {
        "mista": {
            "path": "/mista.html",
            "template": "page.html",
            "json": {"fields": "*"},
        },
    })
    config["site"]["paginate_by"] = 2
    build_site(config, config_dir=tmp_path)

    out = json.loads((tmp_path / "output" / "jsons" / "mista.json").read_text(encoding="utf-8"))
    assert len(out) == 5  # všech 5, ne jen 2 (první stránka)


# ---------------------------------------------------------------------------
# Detail stránky
# ---------------------------------------------------------------------------

def test_detail_page_json_per_record(tmp_path: Path) -> None:
    """Detail stránka generuje jeden JSON objekt per záznam."""
    records = [{"slug": "a", "nazev": "První"}, {"slug": "b", "nazev": "Druhý"}]
    config = _setup(tmp_path, records, {
        "detail": {
            "detail": True,
            "path": "/{{ record.slug }}.html",
            "template": "page.html",
            "json": {"fields": "*"},
        },
    })
    build_site(config, config_dir=tmp_path)

    out_a = json.loads((tmp_path / "output" / "jsons" / "a.json").read_text(encoding="utf-8"))
    out_b = json.loads((tmp_path / "output" / "jsons" / "b.json").read_text(encoding="utf-8"))

    assert isinstance(out_a, dict)
    assert out_a["nazev"] == "První"
    assert out_b["nazev"] == "Druhý"


def test_detail_page_json_field_filter(tmp_path: Path) -> None:
    """Detail JSON respektuje fields whitelist."""
    records = [{"slug": "a", "nazev": "První", "tajne": "x"}]
    config = _setup(tmp_path, records, {
        "detail": {
            "detail": True,
            "path": "/{{ record.slug }}.html",
            "template": "page.html",
            "json": {"fields": ["slug", "nazev"]},
        },
    })
    build_site(config, config_dir=tmp_path)

    out = json.loads((tmp_path / "output" / "jsons" / "a.json").read_text(encoding="utf-8"))
    assert set(out.keys()) == {"slug", "nazev"}


# ---------------------------------------------------------------------------
# Category stránky
# ---------------------------------------------------------------------------

def test_category_page_json_per_category(tmp_path: Path) -> None:
    """Category stránka generuje jeden JSON per kategorii."""
    records = [
        {"slug": "a", "typ": "kriz", "typ_slug": "kriz"},
        {"slug": "b", "typ": "kriz", "typ_slug": "kriz"},
        {"slug": "c", "typ": "socha", "typ_slug": "socha"},
    ]
    config = _setup(tmp_path, records, {
        "typy": {
            "category": "typ",
            "path": "/{{ category.slug }}.html",
            "template": "page.html",
            "json": {"fields": ["slug", "typ"]},
        },
    })
    build_site(config, config_dir=tmp_path)

    out_kriz = json.loads((tmp_path / "output" / "jsons" / "kriz.json").read_text(encoding="utf-8"))
    out_socha = json.loads((tmp_path / "output" / "jsons" / "socha.json").read_text(encoding="utf-8"))

    assert len(out_kriz) == 2
    assert len(out_socha) == 1
    assert all(r["typ"] == "kriz" for r in out_kriz)

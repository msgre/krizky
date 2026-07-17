"""Tests for krizky.site module."""

from __future__ import annotations

import json
import sqlite3
import textwrap
from datetime import datetime
from pathlib import Path

import pytest

from krizky.render import page_path, render_config_str
from krizky.site import SiteError, build_site


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(db_path: Path, records: list[dict], table: str = "data") -> None:
    """Create a SQLite DB with a single table populated from records."""
    if not records:
        return
    cols = list(records[0].keys())
    conn = sqlite3.connect(str(db_path))
    col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
    conn.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({col_defs})')
    placeholders = ", ".join("?" for _ in cols)
    for rec in records:
        conn.execute(
            f'INSERT INTO "{table}" VALUES ({placeholders})',
            [rec.get(c) for c in cols],
        )
    conn.commit()
    conn.close()


def _make_template(tmp_path: Path, name: str, content: str) -> None:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir(exist_ok=True)
    (templates_dir / name).write_text(content, encoding="utf-8")


def _base_config(tmp_path: Path, pages: dict, extra_site: dict | None = None) -> dict:
    """Return a minimal config dict pointing at tmp_path."""
    site_cfg = {
        "title": "Test Site",
        "output": str(tmp_path / "output"),
        "templates": str(tmp_path / "templates"),
        "order_by": "rowid",
        "ordering": "asc",
        "pages": pages,
    }
    if extra_site:
        site_cfg.update(extra_site)
    return {
        "sources": {
            "output": str(tmp_path / "sources"),
            "database": "data.db",
            "tables": {"data": {"main": True}},
        },
        "site": site_cfg,
    }


def _setup(tmp_path: Path, records: list[dict], pages: dict, extra_site: dict | None = None) -> dict:
    """Create DB + templates directories and return a config."""
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()
    _make_db(sources_dir / "data.db", records)
    (tmp_path / "templates").mkdir(exist_ok=True)
    (tmp_path / "output").mkdir(exist_ok=True)
    return _base_config(tmp_path, pages, extra_site)


# ---------------------------------------------------------------------------
# Unit tests for helpers
# ---------------------------------------------------------------------------

def test_page_path_first_page() -> None:
    assert page_path("/mista.html", 1) == "/mista.html"


def test_page_path_second_page() -> None:
    assert page_path("/mista.html", 2) == "/mista-2.html"


def test_page_path_deep_path() -> None:
    assert page_path("/items/mista.html", 3) == "/items/mista-3.html"


def test_render_config_str_simple() -> None:
    assert render_config_str("/{{ record.slug }}.html", record={"slug": "my-slug"}) == "/my-slug.html"


def test_render_config_str_multiple() -> None:
    result = render_config_str("/{{ record.a }}/{{ record.b }}.html", record={"a": "foo", "b": "bar"})
    assert result == "/foo/bar.html"


def test_render_config_str_missing_key() -> None:
    assert render_config_str("/{{ record.missing }}.html", record={}) == "/.html"


def test_render_config_str_cross_table() -> None:
    """Cross-table lookup via tables variable works in config strings."""
    tables = {"typy": {"kriz": {"nazev": "Kříž"}}}
    result = render_config_str(
        "{{ tables.typy[record.typ_slug].nazev }}",
        record={"typ_slug": "kriz"},
        tables=tables,
    )
    assert result == "Kříž"


# ---------------------------------------------------------------------------
# test_simple_page
# ---------------------------------------------------------------------------

def test_simple_page(tmp_path: Path) -> None:
    """A simple page renders filtered records into the template."""
    records = [{"slug": "a", "nazev": "First"}, {"slug": "b", "nazev": "Second"}]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html"},
    })
    _make_template(tmp_path, "all.html", "{% for r in filtered %}{{ r.nazev }},{% endfor %}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    assert "First," in out
    assert "Second," in out


# ---------------------------------------------------------------------------
# test_query_limit
# ---------------------------------------------------------------------------

def test_query_limit(tmp_path: Path) -> None:
    """A page with query.limit only includes the first N records."""
    records = [{"slug": str(i), "nazev": f"Item{i}"} for i in range(5)]
    config = _setup(tmp_path, records, {
        "homepage": {"path": "/index.html", "template": "index.html", "query": {"limit": 2}},
    })
    _make_template(tmp_path, "index.html", "{{ filtered|length }}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "index.html").read_text(encoding="utf-8")
    assert out.strip() == "2"


# ---------------------------------------------------------------------------
# test_query_condition
# ---------------------------------------------------------------------------

def test_query_condition(tmp_path: Path) -> None:
    """A page with query.condition filters to matching records."""
    records = [{"slug": "a", "typ": "kriz"}, {"slug": "b", "typ": "socha"}]
    config = _setup(tmp_path, records, {
        "krize": {"path": "/krize.html", "template": "krize.html", "query": {"condition": "typ = 'kriz'"}},
    })
    _make_template(tmp_path, "krize.html", "{% for r in filtered %}{{ r.slug }},{% endfor %}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "krize.html").read_text(encoding="utf-8")
    assert "a," in out
    assert "b" not in out


# ---------------------------------------------------------------------------
# test_detail_page
# ---------------------------------------------------------------------------

def test_detail_page(tmp_path: Path) -> None:
    """detail: true generates one page per record, with {{ record }} in context."""
    records = [{"slug": "prvni", "nazev": "První"}, {"slug": "druhy", "nazev": "Druhý"}]
    config = _setup(tmp_path, records, {
        "detail": {"detail": True, "path": "/{{ record.slug }}.html", "template": "detail.html"},
    })
    _make_template(tmp_path, "detail.html", "{{ record.nazev }}")

    build_site(config, config_dir=tmp_path)

    assert (tmp_path / "output" / "prvni.html").read_text(encoding="utf-8").strip() == "První"
    assert (tmp_path / "output" / "druhy.html").read_text(encoding="utf-8").strip() == "Druhý"


# ---------------------------------------------------------------------------
# test_category_page
# ---------------------------------------------------------------------------

def test_category_page(tmp_path: Path) -> None:
    """category: generates one page per unique category value."""
    records = [
        {"slug": "a", "typ": "kriz", "typ_slug": "kriz"},
        {"slug": "b", "typ": "kriz", "typ_slug": "kriz"},
        {"slug": "c", "typ": "socha", "typ_slug": "socha"},
    ]
    config = _setup(tmp_path, records, {
        "kategorie": {"category": "typ", "path": "/{{ category.slug }}.html", "template": "kat.html"},
    })
    _make_template(tmp_path, "kat.html", "{{ category.value }}:{% for r in filtered %}{{ r.slug }},{% endfor %}")

    build_site(config, config_dir=tmp_path)

    kriz = (tmp_path / "output" / "kriz.html").read_text(encoding="utf-8")
    socha = (tmp_path / "output" / "socha.html").read_text(encoding="utf-8")
    assert kriz.startswith("kriz:")  # category.value
    assert "a," in kriz and "b," in kriz and "c" not in kriz
    assert socha.startswith("socha:")
    assert "c," in socha and "a," not in socha and "b," not in socha


# ---------------------------------------------------------------------------
# test_category_page_many
# ---------------------------------------------------------------------------

def test_category_page_many(tmp_path: Path) -> None:
    """many: true handles JSON-list category columns."""
    records = [
        {
            "slug": "a",
            "stitky": json.dumps(["priroda", "kamen"]),
            "stitky_slug": json.dumps({"priroda": "priroda", "kamen": "kamen"}),
        },
        {
            "slug": "b",
            "stitky": json.dumps(["priroda"]),
            "stitky_slug": json.dumps({"priroda": "priroda"}),
        },
        {
            "slug": "c",
            "stitky": json.dumps(["kamen"]),
            "stitky_slug": json.dumps({"kamen": "kamen"}),
        },
    ]
    config = _setup(tmp_path, records, {
        "stitky": {
            "category": "stitky",
            "many": True,
            "path": "/{{ category.slug }}.html",
            "template": "stitky.html",
        },
    })
    _make_template(tmp_path, "stitky.html", "{{ category.value }}:{% for r in filtered %}{{ r.slug }},{% endfor %}")

    build_site(config, config_dir=tmp_path)

    priroda = (tmp_path / "output" / "priroda.html").read_text(encoding="utf-8")
    kamen = (tmp_path / "output" / "kamen.html").read_text(encoding="utf-8")
    assert "priroda:" in priroda  # category.value
    assert "a," in priroda and "b," in priroda and "c" not in priroda
    assert "kamen:" in kamen
    assert "a," in kamen and "c," in kamen and "b" not in kamen


# ---------------------------------------------------------------------------
# test_pagination
# ---------------------------------------------------------------------------

def test_pagination(tmp_path: Path) -> None:
    """paginate_by splits records across multiple numbered pages."""
    records = [{"slug": str(i), "nazev": f"Item{i}"} for i in range(5)]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html"},
    }, extra_site={"paginate_by": 2})
    _make_template(tmp_path, "all.html", "{{ pagination.page }}/{{ pagination.total_pages }}:{% for r in filtered %}{{ r.slug }},{% endfor %}")

    build_site(config, config_dir=tmp_path)

    p1 = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    p2 = (tmp_path / "output" / "all-2.html").read_text(encoding="utf-8")
    p3 = (tmp_path / "output" / "all-3.html").read_text(encoding="utf-8")
    assert p1.startswith("1/3:")
    assert p2.startswith("2/3:")
    assert p3.startswith("3/3:")


def test_pagination_nav_urls(tmp_path: Path) -> None:
    """Paginated pages expose correct pagination.prev_url/next_url context variables."""
    records = [{"slug": str(i)} for i in range(4)]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html"},
    }, extra_site={"paginate_by": 2})
    _make_template(tmp_path, "all.html", "prev={{ pagination.prev_url }},next={{ pagination.next_url }}")

    build_site(config, config_dir=tmp_path)

    p1 = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    p2 = (tmp_path / "output" / "all-2.html").read_text(encoding="utf-8")
    assert p1 == "prev=None,next=/all-2.html"
    assert p2 == "prev=/all.html,next=None"


def test_pagination_disabled_per_page(tmp_path: Path) -> None:
    """paginate: false on a page disables global pagination for that page."""
    records = [{"slug": str(i)} for i in range(4)]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html", "paginate": False},
    }, extra_site={"paginate_by": 2})
    _make_template(tmp_path, "all.html", "{{ filtered|length }}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    assert out.strip() == "4"
    assert not (tmp_path / "output" / "all-2.html").exists()


# ---------------------------------------------------------------------------
# test_tables_context
# ---------------------------------------------------------------------------

def test_tables_context(tmp_path: Path) -> None:
    """tables.X is available in template context."""
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()
    _make_db(sources_dir / "data.db", [{"slug": "a", "nazev": "A"}], table="data")
    _make_db(sources_dir / "data.db", [{"key": "claim", "value": "Motto"}], table="snippets")
    # Re-open to add second table to same DB
    conn = sqlite3.connect(str(sources_dir / "data.db"))
    conn.execute('CREATE TABLE IF NOT EXISTS "snippets" ("key" TEXT, "value" TEXT)')
    conn.execute('INSERT INTO "snippets" VALUES (?, ?)', ("claim", "Motto"))
    conn.commit()
    conn.close()

    (tmp_path / "templates").mkdir(exist_ok=True)
    (tmp_path / "output").mkdir(exist_ok=True)

    config = {
        "sources": {
            "output": str(sources_dir),
            "database": "data.db",
            "tables": {
                "data": {"main": True},
                "snippets": {"key": "key"},
            },
        },
        "site": {
            "output": str(tmp_path / "output"),
            "templates": str(tmp_path / "templates"),
            "order_by": "rowid",
            "ordering": "asc",
            "pages": {
                "all": {"path": "/all.html", "template": "all.html"},
            },
        },
    }
    _make_template(tmp_path, "all.html", "{{ tables.snippets.claim.value }}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    assert "Motto" in out


# ---------------------------------------------------------------------------
# test_docs_context
# ---------------------------------------------------------------------------

def test_docs_context(tmp_path: Path) -> None:
    """docs.X is available in template context as string content."""
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()
    _make_db(sources_dir / "data.db", [{"slug": "a"}])
    doc_out = sources_dir / "docs" / "uvod" / "transformed"
    doc_out.mkdir(parents=True)
    (doc_out / "uvod.md").write_text("Hello world", encoding="utf-8")

    (tmp_path / "templates").mkdir()
    (tmp_path / "output").mkdir()

    config = {
        "sources": {
            "output": str(sources_dir),
            "database": "data.db",
            "tables": {"data": {"main": True}},
            "docs": {
                "uvod": {"id": "x", "transform": "x.sh", "output": "uvod.md"},
            },
        },
        "site": {
            "output": str(tmp_path / "output"),
            "templates": str(tmp_path / "templates"),
            "order_by": "rowid",
            "ordering": "asc",
            "pages": {
                "all": {"path": "/all.html", "template": "all.html"},
            },
        },
    }
    _make_template(tmp_path, "all.html", "{{ docs.uvod }}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    assert "Hello world" in out


# ---------------------------------------------------------------------------
# test_assets_copied
# ---------------------------------------------------------------------------

def test_assets_copied(tmp_path: Path) -> None:
    """Assets directory is copied into the output directory."""
    records = [{"slug": "a"}]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html"},
    }, extra_site={"assets": str(tmp_path / "assets")})
    _make_template(tmp_path, "all.html", "ok")

    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "style.css").write_text("body{}", encoding="utf-8")

    build_site(config, config_dir=tmp_path)

    assert (tmp_path / "output" / "assets" / "style.css").exists()


# ---------------------------------------------------------------------------
# test_build_context
# ---------------------------------------------------------------------------

def test_build_assets_url_in_template(tmp_path: Path) -> None:
    """build.assets_url from site config is available in templates."""
    records = [{"slug": "a"}]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html"},
    }, extra_site={"assets_url": "/static/assets"})
    _make_template(tmp_path, "all.html", "{{ build.assets_url }}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    assert out == "/static/assets"


def test_build_assets_url_defaults_to_empty(tmp_path: Path) -> None:
    """build.assets_url defaults to empty string when not set in config."""
    records = [{"slug": "a"}]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html"},
    })
    _make_template(tmp_path, "all.html", "{{ build.assets_url }}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    assert out == ""


def test_build_inline_css_in_template(tmp_path: Path) -> None:
    """build.inline_css contains the contents of assets/css/style.css."""
    records = [{"slug": "a"}]
    assets = tmp_path / "assets"
    (assets / "css").mkdir(parents=True)
    (assets / "css" / "style.css").write_text("body{color:red}", encoding="utf-8")
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html"},
    }, extra_site={"assets": str(assets)})
    _make_template(tmp_path, "all.html", "{{ build.inline_css }}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    assert out == "body{color:red}"


def test_build_inline_css_empty_when_file_missing(tmp_path: Path) -> None:
    """build.inline_css is empty string when assets/css/style.css does not exist."""
    records = [{"slug": "a"}]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html"},
    })
    _make_template(tmp_path, "all.html", "{{ build.inline_css }}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    assert out == ""


def test_build_last_update_in_template(tmp_path: Path) -> None:
    """build.last_update is a datetime object representing the build time."""
    before = datetime.now()
    records = [{"slug": "a"}]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html"},
    })
    _make_template(tmp_path, "all.html", "{{ build.last_update.year }}")

    build_site(config, config_dir=tmp_path)

    after = datetime.now()
    out = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    assert out == str(before.year)
    assert before.year == after.year


# ---------------------------------------------------------------------------
# test_site_context
# ---------------------------------------------------------------------------

def test_site_object_in_template(tmp_path: Path) -> None:
    """site.title, site.description and site.language are available in templates."""
    records = [{"slug": "a"}]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html"},
    }, extra_site={"description": "About us", "language": "cs"})
    _make_template(tmp_path, "all.html", "{{ site.title }}|{{ site.description }}|{{ site.language }}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    assert out == "Test Site|About us|cs"


def test_page_name_in_context(tmp_path: Path) -> None:
    """page_name obsahuje klíč aktuální stránky z config pages."""
    records = [{"slug": "a"}]
    config = _setup(tmp_path, records, {
        "vsechna_mista": {"path": "/mista.html", "template": "page.html"},
    })
    _make_template(tmp_path, "page.html", "{{ page_name }}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "mista.html").read_text(encoding="utf-8")
    assert out == "vsechna_mista"


def test_pages_context(tmp_path: Path) -> None:
    """pages namespace maps page name to its configured path."""
    records = [{"slug": "a"}]
    config = _setup(tmp_path, records, {
        "home":  {"path": "/index.html",        "template": "page.html"},
        "mista": {"path": "/vsechna-mista.html", "template": "page.html"},
    })
    _make_template(tmp_path, "page.html", "{{ page_urls.home }}|{{ page_urls.mista }}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "index.html").read_text(encoding="utf-8")
    assert out == "/index.html|/vsechna-mista.html"


def test_site_title_page_override(tmp_path: Path) -> None:
    """Page-level title is available as site.page_title; site.title stays global."""
    records = [{"slug": "a"}]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html", "title": "Page Title"},
    })
    _make_template(tmp_path, "all.html", "{{ site.page_title }}|{{ site.title }}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    assert out == "Page Title|Test Site"


def test_site_page_title_fallback(tmp_path: Path) -> None:
    """site.page_title falls back to site.title when no page-level title is defined."""
    records = [{"slug": "a"}]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html"},
    })
    _make_template(tmp_path, "all.html", "{{ site.page_title }}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    assert out == "Test Site"


def test_site_title_detail_substitution(tmp_path: Path) -> None:
    """site.page_title is substituted per record on detail pages; site.title stays global."""
    records = [{"slug": "prvni", "name": "První záznam"}, {"slug": "druhy", "name": "Druhý záznam"}]
    config = _setup(tmp_path, records, {
        "detail": {"detail": True, "path": "/{{ record.slug }}.html", "template": "detail.html", "title": "Detail: {{ record.name }}"},
    })
    _make_template(tmp_path, "detail.html", "{{ site.page_title }}|{{ site.title }}")

    build_site(config, config_dir=tmp_path)

    assert (tmp_path / "output" / "prvni.html").read_text(encoding="utf-8") == "Detail: První záznam|Test Site"
    assert (tmp_path / "output" / "druhy.html").read_text(encoding="utf-8") == "Detail: Druhý záznam|Test Site"


def test_site_language_page_override(tmp_path: Path) -> None:
    """Page-level language overrides site.language in the template context."""
    records = [{"slug": "a"}]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html", "language": "en"},
    }, extra_site={"language": "cs"})
    _make_template(tmp_path, "all.html", "{{ site.language }}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    assert out == "en"


def test_site_description_page_override(tmp_path: Path) -> None:
    """Page-level description is in site.page_description; empty value falls back to site.description."""
    records = [
        {"slug": "a", "popis": "Popis záznamu"},
        {"slug": "b", "popis": ""},   # prázdný → fallback na site
    ]
    config = _setup(tmp_path, records, {
        "detail": {"detail": True, "path": "/{{ record.slug }}.html", "template": "detail.html", "description": "{{ record.popis }}"},
    }, extra_site={"description": "Výchozí popis"})
    _make_template(tmp_path, "detail.html", "{{ site.page_description }}|{{ site.description }}")

    build_site(config, config_dir=tmp_path)

    assert (tmp_path / "output" / "a.html").read_text(encoding="utf-8") == "Popis záznamu|Výchozí popis"
    assert (tmp_path / "output" / "b.html").read_text(encoding="utf-8") == "Výchozí popis|Výchozí popis"


def test_site_description_optional(tmp_path: Path) -> None:
    """site.description defaults to empty string when not set."""
    records = [{"slug": "a"}]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html"},
    })
    _make_template(tmp_path, "all.html", "{{ site.description }}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    assert out == ""


# ---------------------------------------------------------------------------
# test_missing_database_raises
# ---------------------------------------------------------------------------

def test_missing_database_raises(tmp_path: Path) -> None:
    """build_site raises SiteError when the database file does not exist."""
    (tmp_path / "sources").mkdir()
    (tmp_path / "templates").mkdir()
    (tmp_path / "output").mkdir()
    config = _base_config(tmp_path, {})

    with pytest.raises(SiteError, match="Database not found"):
        build_site(config, config_dir=tmp_path)


# ---------------------------------------------------------------------------
# test_missing_template_raises
# ---------------------------------------------------------------------------

def test_missing_template_raises(tmp_path: Path) -> None:
    """build_site raises SiteError when a required template does not exist."""
    records = [{"slug": "a"}]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "nonexistent.html"},
    })

    with pytest.raises(SiteError, match="Template not found"):
        build_site(config, config_dir=tmp_path)


# ---------------------------------------------------------------------------
# test_json_column_parsed
# ---------------------------------------------------------------------------

def test_json_column_parsed(tmp_path: Path) -> None:
    """JSON string columns are automatically parsed to Python objects in context."""
    records = [{"slug": "a", "tags": json.dumps(["x", "y"])}]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html"},
    })
    _make_template(tmp_path, "all.html", "{% for r in filtered %}{{ r.tags|join(',') }}{% endfor %}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    assert out.strip() == "x,y"


# ---------------------------------------------------------------------------
# test_ordering
# ---------------------------------------------------------------------------

def test_ordering_desc(tmp_path: Path) -> None:
    """ordering: desc returns records in reverse rowid order."""
    records = [{"slug": "a"}, {"slug": "b"}, {"slug": "c"}]
    config = _setup(tmp_path, records, {
        "all": {"path": "/all.html", "template": "all.html"},
    }, extra_site={"order_by": "rowid", "ordering": "desc"})
    _make_template(tmp_path, "all.html", "{% for r in filtered %}{{ r.slug }}{% endfor %}")

    build_site(config, config_dir=tmp_path)

    out = (tmp_path / "output" / "all.html").read_text(encoding="utf-8")
    assert out == "cba"

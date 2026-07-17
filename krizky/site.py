"""Site generation orchestration for krizky."""

import shutil
import sqlite3
from datetime import date as _date
from datetime import datetime
from pathlib import Path

import jinja2

from krizky.db import DEFAULT_ORDER_BY, DEFAULT_ORDERING, fetch_table
from krizky.markdown import md_filter, mdtext_filter
from krizky.pages import RenderContext, process_page
from krizky.query import QueryRunner
from krizky.render import DEFAULT_PAGINATE_BY, DEFAULT_PAGINATION_BOUNDARY, DEFAULT_PAGINATION_WINDOW, render_config_str


def _strftime(value: object, fmt: str) -> str:
    """Format *value* using strftime *fmt*; parses ISO strings automatically."""
    if isinstance(value, str):
        for pattern in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d.%m.%Y"):
            try:
                value = datetime.strptime(value, pattern)
                break
            except ValueError:
                continue
        else:
            return value  # type: ignore[return-value]
    if isinstance(value, (datetime, _date)):
        return value.strftime(fmt)
    return str(value)


class SiteError(Exception):
    """Raised when site generation fails."""


def build_site(config: dict, config_dir: Path) -> None:
    """Generate HTML pages from the existing SQLite database.

    Args:
        config: Parsed krizky configuration dict.
        config_dir: Directory of the config file; relative paths are resolved
            against it.

    Raises:
        SiteError: If the database or templates directory is missing, or a
            referenced template does not exist.
    """
    sources = config["sources"]
    site = config["site"]

    sources_output = (config_dir / sources["output"]).resolve()
    db_path = sources_output / sources["database"]

    if not db_path.exists():
        raise SiteError(f"Database not found: {db_path}. Run 'krizky fetch sources --transform' first.")

    output_dir = (config_dir / site["output"]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    templates_dir = (config_dir / site["templates"]).resolve()
    if not templates_dir.exists():
        raise SiteError(f"Templates directory not found: {templates_dir}")

    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(templates_dir)),
        autoescape=jinja2.select_autoescape(["html"]),
        keep_trailing_newline=True,
    )
    jinja_env.filters["md"] = md_filter
    jinja_env.filters["mdtext"] = mdtext_filter
    jinja_env.filters["strftime"] = _strftime

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        _generate(config, config_dir, conn, jinja_env, sources_output, output_dir)
    finally:
        conn.close()


def _generate(
    config: dict,
    config_dir: Path,
    conn: sqlite3.Connection,
    jinja_env: jinja2.Environment,
    sources_output: Path,
    output_dir: Path,
) -> None:
    sources = config["sources"]
    site = config["site"]

    order_by = site.get("order_by", DEFAULT_ORDER_BY)
    ordering = site.get("ordering", DEFAULT_ORDERING)
    global_paginate_by = site.get("paginate_by", DEFAULT_PAGINATE_BY)
    pagination_window = site.get("pagination_window", DEFAULT_PAGINATION_WINDOW)
    pagination_boundary = site.get("pagination_boundary", DEFAULT_PAGINATION_BOUNDARY)

    tables_cfg = sources.get("tables", {})
    main_table = next(name for name, tbl in tables_cfg.items() if tbl.get("main"))

    # Load tables and docs first so site.title / site.description can reference them.
    tables_ctx = {
        name: fetch_table(conn, name, key_col=tbl.get("key"))
        for name, tbl in tables_cfg.items()
    }
    docs_ctx = _load_docs(sources.get("docs", {}), sources_output)
    _site_render_ctx = {"tables": tables_ctx, "docs": docs_ctx}

    base_ctx = {
        "tables": tables_ctx,
        "docs": docs_ctx,
        "query": QueryRunner(conn, config.get("queries", {})),
        "page_urls": {
            name: cfg.get("path", "")
            for name, cfg in site.get("pages", {}).items()
        },
        "build": {
            "last_update": datetime.now(),
            "assets_url": site.get("assets_url", ""),
            "inline_css": _load_inline_css(site, config_dir),
        },
        "site": {
            "title": render_config_str(site.get("title", ""), **_site_render_ctx),
            "description": render_config_str(site.get("description", ""), **_site_render_ctx),
            "language": site.get("language", ""),
            "date_format": site.get("date_format", "%-d. %-m. %Y"),
            "time_format": site.get("time_format", "%H:%M:%S"),
            "datetime_format": site.get("datetime_format", "%-d. %-m. %Y %H:%M:%S"),
        },
    }

    _copy_assets(site, config_dir, output_dir)

    for page_name, page_cfg in site.get("pages", {}).items():
        paginate_by = page_cfg.get("paginate_by", global_paginate_by)
        if page_cfg.get("paginate") is False:
            paginate_by = DEFAULT_PAGINATE_BY

        try:
            template = jinja_env.get_template(page_cfg["template"])
        except jinja2.TemplateNotFound:
            raise SiteError(f"Template not found for page '{page_name}': {page_cfg['template']}")

        process_page(
            page_cfg,
            template,
            RenderContext(
                conn=conn,
                main_table=main_table,
                order_by=order_by,
                ordering=ordering,
                output_dir=output_dir,
                base_ctx={**base_ctx, "page_name": page_name},
                paginate_by=paginate_by,
                pagination_window=pagination_window,
                pagination_boundary=pagination_boundary,
            ),
        )


def _load_inline_css(site: dict, config_dir: Path) -> str:
    assets_key = site.get("assets")
    if not assets_key:
        return ""
    css_path = (config_dir / assets_key / "css" / "style.css").resolve()
    if not css_path.exists():
        return ""
    return css_path.read_text(encoding="utf-8")


def _load_docs(docs_cfg: dict, sources_output: Path) -> dict[str, str]:
    result = {}
    for name, doc in docs_cfg.items():
        out_path = sources_output / "docs" / name / "transformed" / doc["output"]
        result[name] = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
    return result


def _copy_assets(site: dict, config_dir: Path, output_dir: Path) -> None:
    assets_key = site.get("assets")
    if not assets_key:
        return
    assets_src = (config_dir / assets_key).resolve()
    if not assets_src.exists():
        return
    assets_dst = output_dir / assets_src.name
    if assets_dst.exists():
        shutil.rmtree(assets_dst)
    shutil.copytree(assets_src, assets_dst)

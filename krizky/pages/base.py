"""Shared types for page processors: RenderContext and PageProcessor."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import jinja2

from krizky.render import render_config_str


def resolve_page_site(
    site: dict,
    page_cfg: dict,
    record: dict | None = None,
    tables: dict | None = None,
    category: dict | None = None,
) -> dict:
    """Return site dict with page-level title/language overrides applied.

    Values are rendered as Jinja2 templates with access to record, tables, category.
    """
    resolved = dict(site)
    ctx: dict = {"record": record or {}, "tables": tables or {}}
    if category is not None:
        ctx["category"] = category
    for key in ("title", "description", "language"):
        if key in page_cfg:
            value = render_config_str(page_cfg[key], **ctx).strip()
            if value:
                resolved[key] = value
    return resolved


@dataclass
class RenderContext:
    """Parameters shared by every page processor."""

    conn: sqlite3.Connection
    main_table: str
    order_by: str
    ordering: str
    output_dir: Path
    base_ctx: dict
    paginate_by: int


class PageProcessor(Protocol):
    """Callable interface implemented by each page type module."""

    def __call__(self, page_cfg: dict, template: jinja2.Template, ctx: RenderContext) -> None: ...

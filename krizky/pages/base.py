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
    """Return site dict extended with page-level title and description.

    ``site.title`` and ``site.description`` always carry the global site values.
    Per-page values (rendered as Jinja2 templates) are stored in
    ``site.page_title`` and ``site.page_description``; they fall back to the
    global values when no page-level key is defined or the rendered value is empty.

    ``site.language`` is still overridable at the page level.
    """
    resolved = dict(site)
    ctx: dict = {"record": record or {}, "tables": tables or {}}
    if category is not None:
        ctx["category"] = category

    # language: still overridable at page level
    if "language" in page_cfg:
        value = render_config_str(page_cfg["language"], **ctx).strip()
        if value:
            resolved["language"] = value

    # title / description: global values are preserved; page-level resolved
    # values are delivered as page_title / page_description
    for key, page_key in (("title", "page_title"), ("description", "page_description")):
        if key in page_cfg:
            value = render_config_str(page_cfg[key], **ctx).strip()
            resolved[page_key] = value if value else site.get(key, "")
        else:
            resolved[page_key] = site.get(key, "")

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
    pagination_window: int = 2
    pagination_boundary: int = 1


class PageProcessor(Protocol):
    """Callable interface implemented by each page type module."""

    def __call__(self, page_cfg: dict, template: jinja2.Template, ctx: RenderContext) -> None: ...

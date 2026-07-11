"""Simple/query page processor."""

import jinja2

from krizky.db import fetch_records
from krizky.pages.base import RenderContext, resolve_page_site
from krizky.render import render_paginated


def render(page_cfg: dict, template: jinja2.Template, ctx: RenderContext) -> None:
    """Render a page with an optional query (condition and/or limit)."""
    query = page_cfg.get("query") or {}
    records = fetch_records(
        ctx.conn,
        ctx.main_table,
        ctx.order_by,
        ctx.ordering,
        condition=query.get("condition"),
        limit=query.get("limit"),
    )
    tables = ctx.base_ctx["tables"]
    site_ctx = resolve_page_site(ctx.base_ctx["site"], page_cfg, tables=tables)
    render_paginated(template, records, page_cfg["path"], ctx.output_dir, ctx.paginate_by, {**ctx.base_ctx, "site": site_ctx},
                     window=ctx.pagination_window, boundary=ctx.pagination_boundary)

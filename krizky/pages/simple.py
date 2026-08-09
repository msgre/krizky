"""Simple/query page processor."""

import jinja2

from krizky.db import fetch_records
from krizky.pages.base import RenderContext, fire_after_page_written, resolve_page_site
from krizky.render import render_paginated


def render(page_cfg: dict, template: jinja2.Template, ctx: RenderContext) -> None:
    """Render a page with an optional query (condition and/or limit)."""
    query = page_cfg.get("query") or {}
    order_by = query.get("order_by", ctx.order_by)
    ordering = query.get("ordering", ctx.ordering)
    records = fetch_records(
        ctx.conn,
        ctx.main_table,
        order_by,
        ordering,
        condition=query.get("condition"),
        limit=query.get("limit"),
    )
    tables = ctx.base_ctx["tables"]
    site_ctx = resolve_page_site(ctx.base_ctx["site"], page_cfg, tables=tables)
    render_paginated(
        template, records, page_cfg["path"], ctx.output_dir, ctx.paginate_by,
        {**ctx.base_ctx, "site": site_ctx,
         "head_injections": ctx.head_injections, "body_end_injections": ctx.body_end_injections},
        window=ctx.pagination_window, boundary=ctx.pagination_boundary,
    )

    fire_after_page_written(ctx, page_cfg, page_cfg["path"], records)

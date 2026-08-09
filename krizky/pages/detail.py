"""Detail page processor — one HTML page per record."""

import jinja2

from krizky.db import fetch_records
from krizky.pages.base import RenderContext, fire_after_page_written, resolve_page_site
from krizky.render import render_config_str


def render(page_cfg: dict, template: jinja2.Template, ctx: RenderContext) -> None:
    """Render one page for every record in the main table."""
    query = page_cfg.get("query") or {}
    order_by = query.get("order_by", ctx.order_by)
    ordering = query.get("ordering", ctx.ordering)
    records = fetch_records(ctx.conn, ctx.main_table, order_by, ordering,
                            condition=query.get("condition"), limit=query.get("limit"))
    tables = ctx.base_ctx["tables"]
    for record in records:
        path = render_config_str(page_cfg["path"], record=record, tables=tables)
        out = ctx.output_dir / path.lstrip("/")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            template.render(
                **{**ctx.base_ctx, "site": resolve_page_site(ctx.base_ctx["site"], page_cfg, record=record, tables=tables)},
                filtered=[record],
                record=record,
                head_injections=ctx.head_injections,
                body_end_injections=ctx.body_end_injections,
            ),
            encoding="utf-8",
        )
        fire_after_page_written(ctx, page_cfg, path, [dict(record)])

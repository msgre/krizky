"""Detail page processor — one HTML page per record."""

import jinja2

from krizky.db import fetch_records
from krizky.json_export import write_json_record
from krizky.pages.base import RenderContext, resolve_page_site
from krizky.render import render_config_str


def render(page_cfg: dict, template: jinja2.Template, ctx: RenderContext) -> None:
    """Render one page for every record in the main table."""
    query = page_cfg.get("query") or {}
    records = fetch_records(ctx.conn, ctx.main_table, ctx.order_by, ctx.ordering,
                            condition=query.get("condition"), limit=query.get("limit"))
    tables = ctx.base_ctx["tables"]
    json_cfg = page_cfg.get("json")
    for record in records:
        path = render_config_str(page_cfg["path"], record=record, tables=tables)
        out = ctx.output_dir / path.lstrip("/")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            template.render(
                **{**ctx.base_ctx, "site": resolve_page_site(ctx.base_ctx["site"], page_cfg, record=record, tables=tables)},
                filtered=[record],
                record=record,
            ),
            encoding="utf-8",
        )
        if json_cfg is not None:
            write_json_record(record, path, ctx.output_dir, json_cfg)

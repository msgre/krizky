"""Category page processor — one page per unique category value."""

import jinja2

from krizky.db import fetch_by_category, fetch_by_tag, fetch_distinct_categories, fetch_distinct_tags
from krizky.pages.base import RenderContext, fire_after_page_written, resolve_page_site
from krizky.render import render_config_str, render_paginated


def render(page_cfg: dict, template: jinja2.Template, ctx: RenderContext) -> None:
    """Render one page per unique value in the category column.

    When *many* is True the category column holds a JSON list and the
    slug column holds a JSON object mapping each value to its slug.
    An optional query.condition restricts both the category discovery
    and the per-category record fetch to the same subset of data.
    """
    cat_col: str = page_cfg["category"]
    slug_col = f"{cat_col}_slug"
    query = page_cfg.get("query") or {}
    condition = query.get("condition")
    limit = query.get("limit")
    order_by = query.get("order_by", ctx.order_by)
    ordering = query.get("ordering", ctx.ordering)
    many = page_cfg.get("many", False)

    fetch_cats = fetch_distinct_tags if many else fetch_distinct_categories
    fetch_recs = fetch_by_tag if many else fetch_by_category

    tables = ctx.base_ctx["tables"]
    for cat_val, cat_slug in fetch_cats(ctx.conn, ctx.main_table, cat_col, slug_col, condition):
        filtered = fetch_recs(ctx.conn, ctx.main_table, order_by, ordering, cat_col, cat_val, condition, limit)
        cat_dict = {"value": cat_val, "slug": cat_slug}
        path = render_config_str(page_cfg["path"], category=cat_dict, tables=tables)
        site_ctx = resolve_page_site(ctx.base_ctx["site"], page_cfg, tables=tables, category=cat_dict)
        render_paginated(
            template, filtered, path, ctx.output_dir, ctx.paginate_by,
            {**ctx.base_ctx, "category": cat_dict, "site": site_ctx},
            window=ctx.pagination_window, boundary=ctx.pagination_boundary,
        )
        fire_after_page_written(ctx, page_cfg, path, filtered)

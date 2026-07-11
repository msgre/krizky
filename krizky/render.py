"""Rendering utilities: config string rendering, path helpers, paginated HTML output."""

from pathlib import Path, PurePosixPath

import jinja2

from krizky.markdown import md_filter, mdtext_filter

DEFAULT_PAGINATE_BY = 0

_config_env = jinja2.Environment(autoescape=False)
_config_env.filters["md"] = md_filter
_config_env.filters["mdtext"] = mdtext_filter


def render_config_str(template_str: str, **ctx) -> str:
    """Render a config string value (path, title, language) as a Jinja2 template.

    Unknown variables resolve to empty string (same behaviour as the old <col> syntax).
    """
    return _config_env.from_string(template_str).render(**ctx)


def page_path(base: str, page_num: int) -> str:
    """Return the file path for a given pagination page number (1-indexed).

    The first page keeps the original name; subsequent pages get a numeric
    suffix before the extension: /mista.html → /mista-2.html, /mista-3.html.
    """
    if page_num == 1:
        return base
    p = PurePosixPath(base)
    return str(p.with_name(f"{p.stem}-{page_num}{p.suffix}"))


def render_paginated(
    template: jinja2.Template,
    records: list[dict],
    base_path: str,
    output_dir: Path,
    paginate_by: int,
    extra_ctx: dict,
) -> None:
    """Render *template* with optional pagination and write the resulting HTML files.

    Args:
        template: Jinja2 template to render.
        records: Full list of records for this page group.
        base_path: Output path (e.g. /mista.html); pagination appends -2, -3, …
        output_dir: Root output directory.
        paginate_by: Records per page; 0 disables pagination.
        extra_ctx: Additional template context (tables, docs, site, …).
    """
    if paginate_by <= 0:
        out = output_dir / base_path.lstrip("/")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            template.render(**extra_ctx, filtered=records, pagination={"paginated": False}),
            encoding="utf-8",
        )
        return

    total_pages = max(1, (len(records) + paginate_by - 1) // paginate_by)
    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * paginate_by
        path = page_path(base_path, page_num)
        ctx = {
            **extra_ctx,
            "filtered": records[start : start + paginate_by],
            "pagination": {
                "paginated": True,
                "page": page_num,
                "total_pages": total_pages,
                "has_prev": page_num > 1,
                "has_next": page_num < total_pages,
                "prev_url": None if page_num == 1 else page_path(base_path, page_num - 1),
                "next_url": None if page_num == total_pages else page_path(base_path, page_num + 1),
            },
        }
        out = output_dir / path.lstrip("/")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(template.render(**ctx), encoding="utf-8")

"""Page processing: type dispatcher and re-exports."""

import krizky.pages.category as category_page
import krizky.pages.detail as detail_page
import krizky.pages.simple as simple_page
from krizky.pages.base import PageProcessor, RenderContext, resolve_page_site

__all__ = ["PageProcessor", "RenderContext", "process_page", "resolve_page_site"]


def process_page(page_cfg: dict, template, ctx: RenderContext) -> None:
    """Dispatch to the correct page processor based on *page_cfg* flags."""
    if page_cfg.get("detail"):
        processor = detail_page.render
    elif page_cfg.get("category"):
        processor = category_page.render
    else:
        processor = simple_page.render
    processor(page_cfg, template, ctx)

"""Jinja2 filters for Markdown rendering and plain-text extraction."""

from html.parser import HTMLParser

from markdown_it import MarkdownIt
from markupsafe import Markup

_md = MarkdownIt()


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(" ".join(self._parts).split())


def md_filter(s: str | None) -> Markup:
    """Render Markdown to HTML (safe for Jinja2 autoescape)."""
    return Markup(_md.render(s or ""))


def mdtext_filter(s: str | None) -> str:
    """Strip Markdown syntax and return plain text."""
    extractor = _TextExtractor()
    extractor.feed(_md.render(s or ""))
    return extractor.get_text()

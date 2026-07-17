"""JSON export alongside HTML page generation."""

import json as _json
from pathlib import Path, PurePosixPath


def _filter_record(record: dict, fields, exclude: list[str]) -> dict:
    if isinstance(fields, list):
        record = {k: v for k, v in record.items() if k in fields}
    if exclude:
        record = {k: v for k, v in record.items() if k not in exclude}
    return record


def _json_out_path(html_path: str, output_dir: Path) -> Path:
    """Return output path for a JSON file mirroring the given HTML path.

    Example: '/mista.html' → <output_dir>/jsons/mista.json
    """
    p = PurePosixPath(html_path.lstrip("/"))
    return output_dir / "jsons" / p.with_suffix(".json")


def write_json_list(
    records: list[dict],
    base_html_path: str,
    output_dir: Path,
    json_cfg: dict,
) -> None:
    """Write a flat JSON array of records to jsons/<base_html_path>.json.

    Pagination is ignored — all records are always exported in one file.
    """
    fields = json_cfg.get("fields", "*")
    exclude: list[str] = json_cfg.get("exclude") or []
    pretty: bool = json_cfg.get("pretty", False)

    data = [_filter_record(dict(r), fields, exclude) for r in records]
    out = _json_out_path(base_html_path, output_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        _json.dumps(data, ensure_ascii=False, indent=2 if pretty else None),
        encoding="utf-8",
    )


def write_json_record(
    record: dict,
    html_path: str,
    output_dir: Path,
    json_cfg: dict,
) -> None:
    """Write a single JSON object to jsons/<html_path>.json (detail pages)."""
    fields = json_cfg.get("fields", "*")
    exclude: list[str] = json_cfg.get("exclude") or []
    pretty: bool = json_cfg.get("pretty", False)

    data = _filter_record(dict(record), fields, exclude)
    out = _json_out_path(html_path, output_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        _json.dumps(data, ensure_ascii=False, indent=2 if pretty else None),
        encoding="utf-8",
    )

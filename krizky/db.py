"""Database access layer for krizky."""

import json
import sqlite3
from typing import Any


DEFAULT_ORDER_BY = "rowid"
DEFAULT_ORDERING = "asc"

# SQLite TRIM(x) only strips spaces. This strips all common whitespace chars.
_SQL_TRIM_WS = "char(9)||char(10)||char(11)||char(12)||char(13)||char(32)"


def _trim(col: str) -> str:
    return f"TRIM([{col}], {_SQL_TRIM_WS})"


def _try_json(value: Any) -> Any:
    """Best-effort JSON parse for string values starting with { or [."""
    if not isinstance(value, str):
        return value
    if not (value.startswith("{") or value.startswith("[")):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError):
        return value


def parse_row(row: dict) -> dict:
    """Parse all values in a row dict, stripping whitespace and converting JSON strings."""
    return {k: _try_json(v.strip() if isinstance(v, str) else v) for k, v in row.items()}


def fetch_records(
    conn: sqlite3.Connection,
    table: str,
    order_by: str = DEFAULT_ORDER_BY,
    ordering: str = DEFAULT_ORDERING,
    condition: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Fetch records from *table* with optional filtering, ordering and limit.

    Args:
        conn: Active SQLite connection.
        table: Table name.
        order_by: Column to sort by (default: rowid).
        ordering: "asc" or "desc" (default: asc).
        condition: Optional SQL WHERE clause (without the WHERE keyword).
        limit: Optional maximum number of rows to return.
    """
    sql = f"SELECT * FROM [{table}]"
    if condition:
        sql += f" WHERE ({condition})"
    # If order_by contains a comma or explicit direction keyword, use it verbatim.
    if "," in order_by or " " in order_by.strip():
        sql += f" ORDER BY {order_by}"
    else:
        sql += f" ORDER BY {order_by} {ordering.upper()}"
    if limit:
        sql += f" LIMIT {limit}"
    return [parse_row(dict(r)) for r in conn.execute(sql).fetchall()]


def fetch_distinct_categories(
    conn: sqlite3.Connection,
    table: str,
    cat_col: str,
    slug_col: str,
    condition: str | None = None,
) -> list[tuple[str, str]]:
    """Return unique (category_value, slug) pairs for a plain-string category column.

    Args:
        conn: Active SQLite connection.
        table: Table name.
        cat_col: Column holding the category string value.
        slug_col: Column holding the corresponding slug string.
        condition: Optional SQL WHERE clause to restrict the source dataset.
    """
    where_parts = [f"{_trim(cat_col)} IS NOT NULL", f"{_trim(cat_col)} != ''"]
    if condition:
        where_parts.append(f"({condition})")
    sql = (
        f"SELECT DISTINCT {_trim(cat_col)}, {_trim(slug_col)} FROM [{table}]"
        f" WHERE {' AND '.join(where_parts)}"
        f" ORDER BY {_trim(cat_col)}"
    )
    return [(row[0].strip() if row[0] else "", row[1].strip() if row[1] else "") for row in conn.execute(sql).fetchall()]


def fetch_distinct_tags(
    conn: sqlite3.Connection,
    table: str,
    cat_col: str,
    slug_col: str,
    condition: str | None = None,
) -> list[tuple[str, str]]:
    """Return unique (tag, slug) pairs from a JSON-list category column.

    Uses SQLite's json_each() to explode JSON arrays into individual rows.

    Args:
        conn: Active SQLite connection.
        table: Table name.
        cat_col: Column holding a JSON array of tag strings.
        slug_col: Column holding a JSON object mapping tag → slug.
        condition: Optional SQL WHERE clause to restrict the source dataset.
    """
    _tv = f"TRIM(je.value, {_SQL_TRIM_WS})"
    where_parts = [f"{_tv} IS NOT NULL", f"{_tv} != ''"]
    if condition:
        where_parts.append(f"({condition})")
    # Fetch tag value + raw slug JSON; slug lookup done in Python because
    # SQLite json_extract dot-path syntax breaks on keys containing '.'.
    sql = (
        f"SELECT DISTINCT {_tv}, t.[{slug_col}]"
        f" FROM [{table}] t, json_each(t.[{cat_col}]) je"
        f" WHERE {' AND '.join(where_parts)}"
    )
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    for tag_raw, slug_json in conn.execute(sql).fetchall():
        tag = tag_raw.strip() if tag_raw else ""
        if not tag or tag in seen:
            continue
        seen.add(tag)
        try:
            slug_dict = json.loads(slug_json) if slug_json else {}
            slug = slug_dict.get(tag, "").strip()
        except (json.JSONDecodeError, AttributeError):
            slug = ""
        result.append((tag, slug))
    return result


def fetch_by_category(
    conn: sqlite3.Connection,
    table: str,
    order_by: str,
    ordering: str,
    cat_col: str,
    cat_val: str,
    condition: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Fetch records where *cat_col* equals *cat_val*, with optional base condition.

    Args:
        conn: Active SQLite connection.
        table: Table name.
        order_by: Column to sort by.
        ordering: "asc" or "desc".
        cat_col: Column to filter on.
        cat_val: Exact value to match.
        condition: Optional additional SQL WHERE clause.
        limit: Optional maximum number of rows to return.
    """
    where_parts = [f"{_trim(cat_col)} = ?"]
    if condition:
        where_parts.append(f"({condition})")
    sql = (
        f"SELECT * FROM [{table}]"
        f" WHERE {' AND '.join(where_parts)}"
        f" ORDER BY {order_by} {ordering.upper()}"
    )
    if limit:
        sql += f" LIMIT {limit}"
    return [parse_row(dict(r)) for r in conn.execute(sql, (cat_val,)).fetchall()]


def fetch_by_tag(
    conn: sqlite3.Connection,
    table: str,
    order_by: str,
    ordering: str,
    cat_col: str,
    tag_val: str,
    condition: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Fetch records where the JSON-list column *cat_col* contains *tag_val*.

    Args:
        conn: Active SQLite connection.
        table: Table name.
        order_by: Column to sort by.
        ordering: "asc" or "desc".
        cat_col: Column holding a JSON array of tag strings.
        tag_val: Tag value that must appear in the array.
        condition: Optional additional SQL WHERE clause.
        limit: Optional maximum number of rows to return.
    """
    where_parts = [f"EXISTS (SELECT 1 FROM json_each([{cat_col}]) je WHERE TRIM(je.value, {_SQL_TRIM_WS}) = ?)"]
    if condition:
        where_parts.append(f"({condition})")
    sql = (
        f"SELECT * FROM [{table}]"
        f" WHERE {' AND '.join(where_parts)}"
        f" ORDER BY {order_by} {ordering.upper()}"
    )
    if limit:
        sql += f" LIMIT {limit}"
    return [parse_row(dict(r)) for r in conn.execute(sql, (tag_val,)).fetchall()]


def fetch_table(
    conn: sqlite3.Connection,
    table: str,
    key_col: str | None = None,
) -> list[dict] | dict[str, dict]:
    """Fetch all rows from *table*, ordered by rowid.

    Args:
        conn: Active SQLite connection.
        table: Table name.
        key_col: When provided, returns a dict keyed by this column's values
            instead of a plain list.
    """
    rows = fetch_records(conn, table)
    if key_col:
        return {row[key_col]: row for row in rows}
    return rows

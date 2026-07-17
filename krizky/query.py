"""Parameterized SQL query runner for Jinja2 template context."""

import logging
import sqlite3

import jinja2

from krizky.db import parse_row

_log = logging.getLogger(__name__)

# Separate Jinja2 env for SQL templates — no HTML filters needed.
_sql_env = jinja2.Environment(autoescape=False)


class _SqlCollector:
    """Accumulates bound parameter values during SQL template rendering."""

    __slots__ = ("values",)

    def __init__(self) -> None:
        self.values: list = []


class _SqlProxy:
    """Wraps a query parameter value for safe SQL interpolation.

    When Jinja2 renders {{ param }}, it calls str() on this proxy.
    The proxy emits '?' (SQLite placeholder) and records the actual value
    in the shared collector — enabling fully parameterized queries.

    Non-proxy values (e.g. {{ limit|default(10) }} where limit is absent)
    render as literals, which is safe because they come from the config file,
    not from external data.
    """

    __slots__ = ("_value", "_collector")

    def __init__(self, value: object, collector: _SqlCollector) -> None:
        self._value = value
        self._collector = collector

    def __str__(self) -> str:
        self._collector.values.append(self._value)
        return "?"

    def __format__(self, spec: str) -> str:
        self._collector.values.append(self._value)
        return "?"

    def __bool__(self) -> bool:
        return bool(self._value)

    def __repr__(self) -> str:
        return f"_SqlProxy({self._value!r})"


def _render_parameterized(sql_template: str, params: dict) -> tuple[str, list]:
    """Render a Jinja2 SQL template into a safe (sql, values) pair.

    Each ``{{ param }}`` reference becomes a ``?`` placeholder; the actual
    value is appended to the returned list in rendering order.

    Non-param expressions — such as ``{{ limit|default(10) }}`` when *limit*
    is absent — render as literals (safe: they originate from the config file).

    Note: arithmetic on proxy values (``{{ latitude + 0.01 }}``) is not
    supported; perform such calculations inside SQL instead.
    """
    collector = _SqlCollector()
    proxy_ctx = {k: _SqlProxy(v, collector) for k, v in params.items()}
    sql = _sql_env.from_string(sql_template).render(**proxy_ctx)
    return sql, collector.values


class QueryRunner:
    """Callable exposed as ``query`` in Jinja2 templates.

    Executes named SQL queries defined in the ``queries:`` config section.
    Results are cached per (name, params) to avoid redundant DB round-trips
    when the same query is called multiple times on a single detail page.

    Usage in templates::

        {% set nearby = query('nearby', latitude=record.latitude, longitude=record.longitude) %}
        {% for place in nearby %}...{% endfor %}
    """

    def __init__(self, conn: sqlite3.Connection, queries_cfg: dict) -> None:
        self._conn = conn
        self._cfg = queries_cfg
        self._cache: dict[tuple, list[dict] | dict[str, dict]] = {}

    def __call__(self, name: str, **params) -> list[dict] | dict[str, dict]:
        try:
            cache_key: tuple | None = (name, tuple(sorted(params.items())))
        except TypeError:
            cache_key = None  # unhashable param values — skip cache

        if cache_key is not None and cache_key in self._cache:
            return self._cache[cache_key]

        query_cfg = self._cfg.get(name)
        if query_cfg is None:
            _log.warning("query(): unknown query name %r — returning []", name)
            return []

        try:
            sql, values = _render_parameterized(query_cfg["sql"], params)
            rows = [parse_row(dict(r)) for r in self._conn.execute(sql, values).fetchall()]
        except Exception as exc:
            _log.error("query(%r, %r): failed — %s", name, params, exc)
            return []

        key_col = query_cfg.get("key")
        result: list[dict] | dict[str, dict] = (
            {row[key_col]: row for row in rows} if key_col else rows
        )

        if cache_key is not None:
            self._cache[cache_key] = result
        return result

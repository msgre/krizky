"""Fetching Google Sheets, Google Docs, and Google Drive photo metadata for krizky."""

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import click


class FetchError(Exception):
    """Raised when an HTTP fetch operation fails."""


class TransformError(Exception):
    """Raised when a transform script exits with a non-zero return code."""


def fetch_sheet(id: str, gid: str, output_path: Path, skip_rows: int = 0) -> None:
    """Download a Google Sheet tab as CSV and write it to *output_path*.

    Args:
        id: The Google Sheets document ID (from the URL).
        gid: The tab/sheet ID (gid= parameter in the URL).
        output_path: Destination file path for the downloaded CSV.
        skip_rows: Number of leading rows to skip from the CSV content.

    Raises:
        FetchError: If the HTTP request fails.
    """
    url = f"https://docs.google.com/spreadsheets/d/{id}/export?format=csv&gid={gid}"
    try:
        with urllib.request.urlopen(url) as response:
            raw_bytes: bytes = response.read()
    except urllib.error.HTTPError as exc:
        raise FetchError(
            f"HTTP error {exc.code} while fetching sheet id={id!r} gid={gid!r}: {exc.reason}"
        ) from exc
    except urllib.error.URLError as exc:
        raise FetchError(
            f"URL error while fetching sheet id={id!r} gid={gid!r}: {exc.reason}"
        ) from exc

    content = raw_bytes.decode("utf-8")
    if skip_rows > 0:
        lines = content.splitlines(keepends=True)
        content = "".join(lines[skip_rows:])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def fetch_doc(id: str, output_path: Path) -> None:
    """Download a Google Doc as DOCX and write it to *output_path*.

    Args:
        id: The Google Docs document ID (from the URL).
        output_path: Destination file path for the downloaded DOCX.

    Raises:
        FetchError: If the HTTP request fails.
    """
    url = f"https://docs.google.com/document/d/{id}/export?format=docx"
    try:
        with urllib.request.urlopen(url) as response:
            raw_bytes: bytes = response.read()
    except urllib.error.HTTPError as exc:
        raise FetchError(
            f"HTTP error {exc.code} while fetching doc id={id!r}: {exc.reason}"
        ) from exc
    except urllib.error.URLError as exc:
        raise FetchError(
            f"URL error while fetching doc id={id!r}: {exc.reason}"
        ) from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(raw_bytes)


def run_transform(
    script: Path,
    source_file: Path,
    db_path: Path,
    table_name: str,
    output_path: Path | None = None,
    skip_rows: int = 0,
) -> None:
    """Execute a bash transform script with the standard krizky arguments.

    Args:
        script: Path to the bash script to run.
        source_file: Passed as $1 to the script.
        db_path: Passed as $2 to the script.
        table_name: Passed as $3 to the script.
        output_path: Passed as $4 to the script; empty string if None.
        skip_rows: Passed as $5 to the script; 0 if not applicable.

    Raises:
        TransformError: If the script exits with a non-zero return code.
    """
    result = subprocess.run(
        [
            str(script),
            str(source_file),
            str(db_path),
            table_name,
            str(output_path) if output_path is not None else "",
            str(skip_rows),
        ],
        check=False,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    if result.returncode != 0:
        raise TransformError(
            f"Transform script '{script}' exited with code {result.returncode}"
        )



def fetch_sources(config: dict, config_dir: Path, transform: bool = False, pm=None) -> None:
    """Orchestrate fetching all tables and docs defined in *config*.

    Args:
        config: Parsed krizky configuration dict.
        config_dir: Directory of the config file; relative paths are resolved
            against it.
        transform: When True, run transform scripts after each fetch.

    Raises:
        FetchError: If any HTTP fetch fails.
        TransformError: If any transform script fails or its output is missing.
    """
    sources = config["sources"]
    sources_output: Path = (config_dir / sources["output"]).resolve()
    db_path: Path = sources_output / sources["database"]

    # --- Tables ---
    for name, table in sources.get("tables", {}).items():
        out_dir = sources_output / "tables" / name / "source"
        out_dir.mkdir(parents=True, exist_ok=True)
        csv_path = out_dir / f"{name}.csv"

        fetch_sheet(table["id"], table["gid"], csv_path, table.get("skip_rows", 0))
        click.echo(f"  Fetched table '{name}' → {csv_path}")

        if transform and table.get("transform"):
            script = (config_dir / table["transform"]).resolve()
            transformed_dir = sources_output / "tables" / name / "transformed"
            transformed_dir.mkdir(parents=True, exist_ok=True)
            run_transform(script, csv_path, db_path, name, skip_rows=table.get("skip_rows", 0))

    # --- Docs ---
    for name, doc in sources.get("docs", {}).items():
        out_dir = sources_output / "docs" / name / "source"
        out_dir.mkdir(parents=True, exist_ok=True)
        docx_path = out_dir / f"{name}.docx"

        fetch_doc(doc["id"], docx_path)
        click.echo(f"  Fetched doc '{name}' → {docx_path}")

        if transform and doc.get("transform"):
            script = (config_dir / doc["transform"]).resolve()
            output_path = sources_output / "docs" / name / "transformed" / doc["output"]
            output_path.parent.mkdir(parents=True, exist_ok=True)
            run_transform(script, docx_path, db_path, name, output_path, skip_rows=0)
            if not output_path.exists():
                raise TransformError(
                    f"Transform script for doc '{name}' did not produce expected output: {output_path}"
                )

    if pm is not None:
        pm.hook.after_sources_fetched(
            config=config,
            config_dir=config_dir,
            sources_output=sources_output,
        )

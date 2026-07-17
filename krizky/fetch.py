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


def fetch_gdrive_metadata(config: dict, config_dir: Path) -> list[dict]:
    """Fetch the list of photo files from a Google Drive folder.

    Requires optional dependencies: pip install krizky[photos]

    Reads ``sources.photos.source`` from *config*, lists all files in the
    configured Drive folder, and saves the result to
    ``<sources.output>/photos/gdrive_metadata.json``.

    The metadata file is committed to the repository and serves as the
    source of truth for change detection in ``krizky build photos``.

    Args:
        config: Parsed krizky configuration dict.
        config_dir: Directory of the config file.

    Returns:
        List of photo metadata dicts with keys: title, last_modified,
        file_id, row_number.

    Raises:
        FetchError: If Google Drive access fails or optional deps are missing.
    """
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build as _build
    except ImportError:
        raise FetchError(
            "google-api-python-client and google-auth are required for photo fetching. "
            "Install with: pip install krizky[photos]"
        )

    photos_cfg = config.get("sources", {}).get("photos")
    if not photos_cfg:
        raise FetchError("No 'sources.photos' section found in config")

    source_cfg = photos_cfg["source"]
    folder_id: str = source_cfg["folder_id"]
    account_key: str = source_cfg["account_key"]
    scopes = ["https://www.googleapis.com/auth/drive.readonly"]

    # account_key can be a JSON string (CI/CD) or a path to a JSON file.
    try:
        key_data = json.loads(account_key)
        creds = Credentials.from_service_account_info(key_data, scopes=scopes)
    except (json.JSONDecodeError, ValueError):
        key_path = Path(account_key)
        if not key_path.is_absolute():
            key_path = (config_dir / account_key).resolve()
        creds = Credentials.from_service_account_file(str(key_path), scopes=scopes)

    service = _build("drive", "v3", credentials=creds)

    results: list[dict] = []
    page_token = None
    while True:
        response = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="nextPageToken, files(id, name, modifiedTime)",
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            pageSize=1000,
        ).execute()

        for f in response.get("files", []):
            row_number = _parse_photo_row_number(f["name"])
            if row_number is None:
                continue
            results.append({
                "title": f["name"],
                "last_modified": f["modifiedTime"],
                "file_id": f["id"],
                "row_number": row_number,
            })

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    # Persist to sources/photos/gdrive_metadata.json.
    sources_output = (config_dir / config["sources"]["output"]).resolve()
    out_path = sources_output / "photos" / "gdrive_metadata.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    return results


def _parse_photo_row_number(filename: str) -> int | None:
    """Return the row number from a photo filename, or None if not a photo file."""
    import re
    stem = Path(filename).stem
    m = re.match(r"^(\d+)(-\d+)?$", stem, re.IGNORECASE)
    return int(m.group(1)) if m else None


def fetch_sources(config: dict, config_dir: Path, transform: bool = False) -> None:
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

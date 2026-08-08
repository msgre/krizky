"""Click CLI entry point for krizky."""

import logging
import shutil
from pathlib import Path

import click

from krizky.config import ConfigError, load_config, validate_config

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")


# ---------------------------------------------------------------------------
# Templates used by `krizky init`
# ---------------------------------------------------------------------------

_CONFIG_YAML_TEMPLATE = """\
# krizky configuration file
# See https://github.com/your-org/krizky for full documentation.

sources:
    # Directory where downloaded source files are stored (gitignored).
    output: ./sources

    # SQLite database file produced by transform scripts.
    database: data.db

    tables:
        # Each key here becomes a table name in the SQLite database.
        data:
            # Google Sheets document ID (from the URL).
            id: "YOUR_SHEET_ID"
            # Tab ID within the document (gid= parameter in the URL).
            gid: "0"
            # Skip N leading rows before the actual data begins.
            skip_rows: 3
            # Exactly one table must be marked as the main dataset.
            main: true
            # Optional bash script that transforms the raw CSV into the DB.
            transform: ./transforms/data.sh

        snippets:
            id: "YOUR_SHEET_ID"
            gid: "123456"
            # Column whose values become dict keys in Jinja2 context.
            key: key
            transform: ./transforms/snippets.sh

    docs:
        # Each key here becomes a variable available as {{ docs.<key> }}.
        uvod:
            id: "YOUR_DOC_ID"
            # Transform script is required for docs entries.
            transform: ./transforms/uvod.sh
            # Output filename produced by the transform script (required).
            output: uvod.md

    photos:
        base_url: https://photos.example.com
        source:
            type: gdrive
            folder_id: YOUR_GDRIVE_FOLDER_ID
            # Sensitive values: use $ENV_VAR_NAME syntax.
            account_key: $GDRIVE_ACCOUNT_KEY
            metadata: ./sources/photos/gdrive_metadata.json
        destination:
            type: cloudflare
            bucket: YOUR_BUCKET_NAME
            account_id: $CF_ACCOUNT_ID
            access_key_id: $CF_ACCESS_KEY_ID
            secret_access_key: $CF_SECRET_ACCESS_KEY
            metadata: ./sources/photos/cf_metadata.json
        formats:
            - format: avif
              mime: image/avif
              quality: 60
            - format: webp
              mime: image/webp
              quality: 80
            - format: jpg
              mime: image/jpeg
              optimalizator: cjpeg
              quality: 80
        sizes:
            - name: micro
              max_width: 150
            - name: thumb
              max_width: 330
            - name: small
              max_width: 680
            - name: medium
              max_width: 960
            - name: big
              max_width: 1600

site:
    # Human-readable site title — available in templates as {{ site.title }}.
    title: My krizky Site
    # Short description inserted into <meta name="description"> (optional).
    description: A short description of this site.
    # BCP 47 language tag used in <html lang="…"> (optional).
    language: cs
    # strftime format strings for use in templates (optional).
    date_format: "%-d. %-m. %Y"
    time_format: "%H:%M:%S"
    datetime_format: "%-d. %-m. %Y %H:%M:%S"
    base_url: https://example.com
    # Directory with static assets (CSS, JS, fonts, images).
    assets: ./assets
    # Base URL for assets as used in templates (e.g. /assets or https://cdn.example.com/assets).
    assets_url: /assets
    # Output directory for generated HTML pages.
    output: ./docs/
    # Global pagination (number of records per page).
    paginate_by: 10
    # Column to sort records by (default: rowid).
    order_by: rowid
    # Sort direction: asc or desc.
    ordering: desc
    # Directory containing Jinja2 templates.
    templates: ./templates

    pages:
        homepage:
            query:
                limit: 10
            path: /index.html
            template: index.html

        all:
            path: /all.html
            template: all.html

        detail:
            detail: true
            path: "/{{ record.slug }}.html"
            title: "{{ record.nazev }} — My krizky Site"
            template: detail.html
"""

_ENV_EXAMPLE_TEMPLATE = """\
# Google Drive service account key file path
GDRIVE_ACCOUNT_KEY=

# Cloudflare R2 credentials
CF_ACCOUNT_ID=
CF_ACCESS_KEY_ID=
CF_SECRET_ACCESS_KEY=
"""


# ---------------------------------------------------------------------------
# CLI definition
# ---------------------------------------------------------------------------

@click.group()
@click.option(
    "--config",
    default="config.yaml",
    show_default=True,
    help="Path to the YAML configuration file.",
)
@click.pass_context
def cli(ctx: click.Context, config: str) -> None:
    """krizky — static site generator from Google Sheets, Docs and Drive."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = config


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

@cli.command()
@click.pass_context
def validate(ctx: click.Context) -> None:
    """Validate the configuration file."""
    config_path: str = ctx.obj["config"]
    try:
        config = load_config(config_path)
        validate_config(config, config_dir=Path(config_path).parent)
    except ConfigError as exc:
        click.echo(click.style(f"ERROR: {exc.message}", fg="red"))
        raise SystemExit(1) from None
    except Exception as exc:  # noqa: BLE001
        click.echo(click.style(f"ERROR: {exc}", fg="red"))
        raise SystemExit(1) from None

    click.echo(click.style("OK: Configuration is valid.", fg="green"))


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("directory", default=".", type=click.Path())
def init(directory: str) -> None:
    """Initialise a new krizky project in DIRECTORY (default: current dir)."""
    target = Path(directory).resolve()
    target.mkdir(parents=True, exist_ok=True)

    # Check if directory is non-empty
    existing = list(target.iterdir())
    if existing:
        click.confirm(
            f"Directory '{target}' is not empty. Continue anyway?",
            abort=True,
        )

    # Generate config.yaml
    config_file = target / "config.yaml"
    config_file.write_text(_CONFIG_YAML_TEMPLATE, encoding="utf-8")
    click.echo(f"Created {config_file}")

    # Generate .env.example
    env_example = target / ".env.example"
    env_example.write_text(_ENV_EXAMPLE_TEMPLATE, encoding="utf-8")
    click.echo(f"Created {env_example}")

    # Create standard directories
    for dirname in ("templates", "assets", "transforms"):
        d = target / dirname
        d.mkdir(exist_ok=True)
        click.echo(f"Created {d}/")

    click.echo(click.style("\nProject initialised successfully.", fg="green"))
    click.echo("Next steps:")
    click.echo("  1. Edit config.yaml with your Google Sheets/Docs IDs.")
    click.echo("  2. Copy .env.example to .env and fill in your credentials.")
    click.echo("  3. Add Jinja2 templates to the templates/ directory.")


# ---------------------------------------------------------------------------
# fetch group
# ---------------------------------------------------------------------------

@cli.group()
def fetch() -> None:
    """Fetch data from remote sources."""


@fetch.command("sources")
@click.option("--transform", is_flag=True, default=False, help="Run transform scripts after fetching.")
@click.pass_context
def fetch_sources(ctx: click.Context, transform: bool) -> None:
    """Download tables and documents from Google."""
    config_path = ctx.obj["config"]
    try:
        config = load_config(config_path)
        validate_config(config, config_dir=Path(config_path).parent)
    except ConfigError as exc:
        click.echo(click.style(f"ERROR: {exc.message}", fg="red"))
        raise SystemExit(1) from None

    from krizky.fetch import FetchError, TransformError, fetch_sources as _fetch_sources
    from krizky.plugin_manager import get_plugin_manager
    try:
        click.echo("Fetching sources...")
        config_dir = Path(config_path).parent
        pm = get_plugin_manager(config_dir)
        _fetch_sources(config, config_dir=config_dir, transform=transform, pm=pm)
        click.echo(click.style("OK: Sources fetched successfully.", fg="green"))
    except (FetchError, TransformError) as exc:
        click.echo(click.style(f"ERROR: {exc}", fg="red"))
        raise SystemExit(1) from None


# ---------------------------------------------------------------------------
# build group
# ---------------------------------------------------------------------------

@cli.group(invoke_without_command=True)
@click.option("--force", is_flag=True, default=False, help="Skip change detection, force full rebuild.")
@click.option("--dry-run", is_flag=True, default=False, help="Show what would happen without doing it.")
@click.pass_context
def build(ctx: click.Context, force: bool, dry_run: bool) -> None:
    """Build the site (complete build)."""
    if ctx.invoked_subcommand is None:
        click.echo("not implemented")


@build.command("site")
@click.option("--force", is_flag=True, default=False, help="Skip change detection, force full rebuild.")
@click.option("--dry-run", is_flag=True, default=False, help="Show what would happen without doing it.")
@click.option("--verbose", "-v", is_flag=True, default=False, help="Show debug info (resolved paths, loaded files, …).")
@click.pass_context
def build_site(ctx: click.Context, force: bool, dry_run: bool, verbose: bool) -> None:
    """Generate HTML pages from existing database."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config_path = ctx.obj["config"]
    try:
        config = load_config(config_path)
        validate_config(config, config_dir=Path(config_path).parent)
    except ConfigError as exc:
        click.echo(click.style(f"ERROR: {exc.message}", fg="red"))
        raise SystemExit(1) from None

    if verbose:
        config_dir = Path(config_path).parent
        sources_output = (config_dir / config["sources"]["output"]).resolve()
        photos_dir = sources_output / "photos"
        click.echo(f"  config dir:      {config_dir}")
        click.echo(f"  sources output:  {sources_output}")
        click.echo(f"  photos dir:      {photos_dir}")
        click.echo(f"  cf_metadata:     {photos_dir / 'cf_metadata.json'} {'✓' if (photos_dir / 'cf_metadata.json').exists() else '✗ MISSING'}")
        click.echo(f"  focal_points:    {photos_dir / 'focal_points.json'} {'✓' if (photos_dir / 'focal_points.json').exists() else '✗ MISSING'}")

    from krizky.site import SiteError, build_site as _build_site
    try:
        click.echo("Building site...")
        _build_site(config, config_dir=Path(config_path).parent)
        click.echo(click.style("OK: Site built successfully.", fg="green"))
    except SiteError as exc:
        click.echo(click.style(f"ERROR: {exc}", fg="red"))
        raise SystemExit(1) from None


# ---------------------------------------------------------------------------
# Plugin hook: register_commands
# Allow installed (entry-point) plugins to add CLI commands.
# Local plugins/ dir is not loaded here — config_dir is not yet known.
# ---------------------------------------------------------------------------

from krizky.plugin_manager import get_plugin_manager as _get_pm  # noqa: E402
_get_pm().hook.register_commands(cli=cli)

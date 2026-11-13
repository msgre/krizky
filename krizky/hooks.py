"""Plugin hook specifications for krizky."""

import pluggy

hookspec = pluggy.HookspecMarker("krizky")
hookimpl = pluggy.HookimplMarker("krizky")


class KrizkySpec:
    """Defines the krizky plugin API surface."""

    @hookspec
    def prepare_jinja2_environment(self, env, config, config_dir):
        """Add filters, globals, or extensions to the Jinja2 environment.

        Called once per build after core filters (md, mdtext, strftime) are
        registered but before any page is rendered. All implementations are called.

        Args:
            env: jinja2.Environment instance.
            config: Parsed krizky config dict.
            config_dir: Path to the directory containing config.yaml.
        """

    @hookspec
    def extra_template_vars(self, config, config_dir, conn):
        """Return extra variables to merge into every template's base context.

        All implementations are called; each may return a dict or None.
        Returned dicts are merged in registration order (later wins on conflict).

        Args:
            config: Parsed krizky config dict.
            config_dir: Path to the directory containing config.yaml.
            conn: Open sqlite3.Connection to the data database.
        """

    @hookspec
    def register_commands(self, cli):
        """Add Click commands or groups to the top-level krizky CLI.

        Called once at CLI startup. Only installed (entry-point) plugins are
        available here — local plugins/ dir is not loaded at this point
        because config_dir is not yet known.

        Args:
            cli: The root click.Group instance.
        """

    @hookspec
    def after_page_written(self, page_cfg, html_path, output_dir, records, config):
        """Called after each logical page (or per-record file) is written.

        Firing semantics per page type:
        - Simple pages: once per page definition; records = all records.
        - Category pages: once per category value; records = filtered records.
        - Detail pages: once per record; records = [record].

        All implementations are called.

        Args:
            page_cfg: Page configuration dict from config.yaml.
            html_path: Logical HTML path string (e.g. '/mista.html').
                       Used by plugins to compute sidecar file paths.
            output_dir: Path to the site output directory.
            records: List of record dicts rendered on this logical page.
            config: Full krizky config dict.
        """

    @hookspec
    def inject_head(self, page_cfg, config):
        """Return an HTML string to inject into <head> for this page, or None.

        Called once per page definition before rendering. All implementations
        are called; results are concatenated in registration order.

        Use this to inject <link>, <meta>, or <style> tags that apply only to
        pages matching a specific config key (e.g. ``filters``).

        Args:
            page_cfg: Page configuration dict from config.yaml.
            config: Full krizky config dict.
        """

    @hookspec
    def inject_body_end(self, page_cfg, config):
        """Return an HTML string to inject before </body> for this page, or None.

        Called once per page definition before rendering. All implementations
        are called; results are concatenated in registration order.

        Use this to inject <script> tags or inline data that apply only to
        pages matching a specific config key (e.g. ``filters``).

        Args:
            page_cfg: Page configuration dict from config.yaml.
            config: Full krizky config dict.
        """

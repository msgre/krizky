"""Plugin manager factory for krizky."""

from __future__ import annotations

import importlib.metadata
import importlib.util
from pathlib import Path

import pluggy

from krizky.hooks import KrizkySpec


def get_plugin_manager(config_dir: Path | None = None) -> pluggy.PluginManager:
    """Build and return a PluginManager with all plugins loaded.

    Discovery order (highest priority first):
    1. Local plugins/ directory — per-project plugins, no packaging required.
       Each .py file must expose a module-level ``plugin`` object with
       @hookimpl-decorated methods.
    2. Installed entry-point plugins via [project.entry-points."krizky"].
    3. Built-in plugins bundled with krizky (always registered).

    Args:
        config_dir: When provided, loads plugins from <config_dir>/plugins/*.py.

    Returns:
        Configured pluggy.PluginManager.
    """
    pm = pluggy.PluginManager("krizky")
    pm.add_hookspecs(KrizkySpec)

    # Local plugins/ directory — registered first (highest priority).
    if config_dir is not None:
        plugins_dir = config_dir / "plugins"
        if plugins_dir.is_dir():
            for py_file in sorted(plugins_dir.glob("*.py")):
                spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
                spec.loader.exec_module(mod)  # type: ignore[union-attr]
                if hasattr(mod, "plugin"):
                    pm.register(mod.plugin)

    # Installed package plugins via Python entry points.
    for ep in importlib.metadata.entry_points(group="krizky"):
        plugin_obj = ep.load()
        pm.register(plugin_obj)

    # No built-in plugins currently registered.
    # JsonExportPlugin moved to krizky-json package.
    # PhotosPlugin moved to krizky-photos package.

    return pm

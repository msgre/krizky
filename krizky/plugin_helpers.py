"""Helper functions for krizky plugins."""

import shutil
from pathlib import Path

import jinja2


def register_plugin_templates(env: jinja2.Environment, templates_dir: str | Path) -> None:
    """Insert a plugin's templates directory into the Jinja2 ChoiceLoader chain.

    The loader is placed right after the first loader (project templates) and
    before the built-in krizky templates. Calling it repeatedly with the same
    path adds the loader only once. If ``env.loader`` is not a ChoiceLoader,
    nothing happens.

    Args:
        env: Jinja2 environment.
        templates_dir: Path to the plugin's templates directory.
    """
    if not isinstance(env.loader, jinja2.ChoiceLoader):
        return
    path = str(Path(templates_dir))
    for loader in env.loader.loaders:
        if isinstance(loader, jinja2.FileSystemLoader) and path in (
            str(Path(p)) for p in loader.searchpath
        ):
            return
    env.loader.loaders.insert(1, jinja2.FileSystemLoader(path))


def replace_tree(source: str | Path, target: str | Path) -> None:
    """Copy directory ``source`` to ``target``, replacing ``target`` if it exists.

    Stale files in ``target`` are removed. Missing parent directories of
    ``target`` are created.

    Args:
        source: Directory to copy.
        target: Destination directory.
    """
    target = Path(target)
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def resolve_path(path: str | Path | None, config_dir: str | Path) -> Path | None:
    """Convert a path from config to an absolute path.

    Args:
        path: Path from config; relative paths are relative to ``config_dir``.
        config_dir: Directory containing config.yaml.

    Returns:
        Resolved absolute path, or None if ``path`` is None or empty.
    """
    if path is None or path == "":
        return None
    p = Path(path)
    if not p.is_absolute():
        p = Path(config_dir) / p
    return p.resolve()

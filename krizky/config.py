"""Configuration loading and validation for krizky."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class ConfigError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _substitute_env(value: Any) -> Any:
    """Recursively substitute ENV variable references in config values.

    String values starting with '$' are replaced by the corresponding
    environment variable. Raises ConfigError if the variable is not set.
    """
    if isinstance(value, str):
        if value.startswith("$"):
            var_name = value[1:]
            env_value = os.environ.get(var_name)
            if env_value is None:
                raise ConfigError(
                    f"Environment variable '{var_name}' is not set "
                    f"(referenced as '{value}' in config)"
                )
            return env_value
        return value
    elif isinstance(value, dict):
        return {k: _substitute_env(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_substitute_env(item) for item in value]
    else:
        return value


def load_config(path: str) -> dict:
    """Load YAML configuration from *path*, substituting ENV variables.

    Also loads a .env file from the current working directory if one exists.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        Parsed and ENV-substituted configuration as a dict.

    Raises:
        ConfigError: If the file cannot be read, is not valid YAML, or an
            ENV variable referenced in the config is not set.
    """
    config_path = Path(path)

    # Load .env from the config file's directory first, then fall back to CWD.
    load_dotenv(config_path.parent / ".env", override=False)
    load_dotenv(override=False)
    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {path}")

    try:
        with config_path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Failed to parse YAML configuration: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError(f"Configuration file must contain a YAML mapping, got: {type(raw).__name__}")

    return _substitute_env(raw)


def validate_config(config: dict, config_dir: Path | None = None) -> None:
    """Validate the loaded configuration.

    Checks:
    - Sections 'sources' and 'site' exist.
    - In 'sources.tables' exactly one table has 'main: true'.
    - Paths to transform scripts (if provided) exist on disk.
    - For each 'docs' entry: required attributes 'transform' and 'output' are present.

    Args:
        config: Configuration dict as returned by load_config().
        config_dir: Directory of the config file; relative paths in the config
            are resolved against it. Defaults to CWD.

    Raises:
        ConfigError: If any validation check fails.
    """
    base = (config_dir or Path(".")).resolve()

    def resolve(p: str) -> Path:
        return (base / p).resolve()

    # Check required top-level sections
    if "sources" not in config:
        raise ConfigError("Missing required section 'sources' in configuration")
    if "site" not in config:
        raise ConfigError("Missing required section 'site' in configuration")

    sources = config["sources"]

    # Validate sources.tables
    tables = sources.get("tables") or {}
    main_tables = [name for name, tbl in tables.items() if tbl.get("main") is True]

    if len(main_tables) == 0:
        raise ConfigError(
            "Configuration must have exactly one table with 'main: true' in 'sources.tables', "
            "but none was found"
        )
    if len(main_tables) > 1:
        raise ConfigError(
            f"Configuration must have exactly one table with 'main: true' in 'sources.tables', "
            f"but found {len(main_tables)}: {', '.join(main_tables)}"
        )

    # Validate transform script paths for tables
    for name, tbl in tables.items():
        transform = tbl.get("transform")
        if transform:
            script_path = resolve(transform)
            if not script_path.exists():
                raise ConfigError(
                    f"Transform script for table '{name}' does not exist: {script_path}"
                )

    # Validate docs entries
    docs = sources.get("docs") or {}
    for name, doc in docs.items():
        if not isinstance(doc, dict):
            raise ConfigError(f"docs entry '{name}' must be a mapping")
        if "transform" not in doc:
            raise ConfigError(
                f"docs entry '{name}' is missing required attribute 'transform'"
            )
        if "output" not in doc:
            raise ConfigError(
                f"docs entry '{name}' is missing required attribute 'output'"
            )
        transform = doc.get("transform")
        if transform:
            script_path = resolve(transform)
            if not script_path.exists():
                raise ConfigError(
                    f"Transform script for doc '{name}' does not exist: {script_path}"
                )

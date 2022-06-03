"""Mypy configuration module."""
from pathlib import Path
from typing import Any, Dict

from tomlkit import dump, load, table
from tomlkit.toml_document import TOMLDocument


def add_property(document: TOMLDocument, key: str, value: Any) -> None:
    """Add a property to a TOMLDocument."""
    config: Dict[str, Any] = document

    keys = key.split('.')

    for i, k in enumerate(keys):
        if k not in config and i < len(keys) - 1:
            config[k] = table()

        if i == len(keys) - 1:
            config[k] = value
            break

        config = config[k]


def setup_mypy_config(pyproject_path: Path) -> None:
    """Setup mypy configuration with sane defaults.

    Args:
        pyproject_path: Path to the pyproject.toml file to edit.
    """
    with pyproject_path.open() as pyproject_file:
        pyproject = load(pyproject_file)

    add_property(pyproject, 'tool.mypy.strict', True)

    with pyproject_path.open('w') as pyproject_file:
        dump(pyproject, pyproject_file)

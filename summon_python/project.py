"""Functions for getting Python-project related information."""
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, TypeVar, Union, cast

import toml
from summon.error import SummonError
from summon.project import reverse_directory_search
from typing_extensions import TypeGuard

TomlArray = List[Any]
TomlDict = Dict[str, Any]
TomlObject = Union[bool, float, int, str, TomlArray, TomlDict]


class TomlValueTypeError(SummonError):
    """Signal that a value read from Toml was of the wrong type."""


def read_toml_variable(
    toml_dict: TomlDict, path: Iterable[str]
) -> Optional[TomlObject]:
    """Read a variable from a dict loaded from a Toml file."""

    obj: Any = toml_dict

    for p in path:
        if not isinstance(obj, dict):
            return None

        obj = obj.get(p)

    return cast(TomlObject, obj)


def is_list_str(obj: object) -> TypeGuard[List[str]]:
    """Type assertion for asserting that an object is a list of strings."""
    return isinstance(obj, list) and all(isinstance(s, str) for s in obj)


def read_package_name_from_poetry(toml_dict: TomlDict) -> Optional[str]:
    """Read the package name from Poetry, given the pyproject.toml convention."""
    package_name = read_toml_variable(toml_dict, ['tool', 'poetry', 'name'])

    if package_name is not None and not isinstance(package_name, str):
        raise TomlValueTypeError()

    if package_name is None:
        return None

    return package_name.replace('-', '_')


class ProjectFileMissingError(SummonError):
    """Signal that the project file containing information was not found."""


class TomlValueMissingError(SummonError):
    """Signal that a value expected in the toml file was missing."""


def get_extra_modules_from_toml(toml_dict: TomlDict) -> List[str]:
    """Get extra modules that should be linted/formatted.

    Extras are modules that aren't part of the main project, such as helper scripts.
    """
    extras = read_toml_variable(
        toml_dict, ['tool', 'summon', 'plugins', 'python', 'extra-modules']
    )

    if extras is None:
        return []

    if not is_list_str(extras):
        raise TomlValueTypeError()

    return extras


def get_packages_glob_pattern_from_package_entry(toml_dict: TomlDict) -> str:
    """Get the glob pattern from a pyproject.toml Poetry entry in packages`."""
    if 'from' not in toml_dict:
        return toml_dict['include']

    return os.sep.join((toml_dict['from'], toml_dict['include']))


def get_package_paths_from_toml(toml_dict: TomlDict, *, base_path: Optional[Path] = None) -> Optional[List[Path]]:
    """Get the path of all packages specified according to the Poetry specification."""
    base_path = base_path if base_path is not None else Path.cwd()

    package_entries = read_toml_variable(toml_dict, ['tool', 'poetry', 'packages'])

    if package_entries is not None and isinstance(package_entries, list):
        return [
            p
            for entry in package_entries
            for p in base_path.glob(get_packages_glob_pattern_from_package_entry(entry))
        ]

    package_name = read_package_name_from_poetry(toml_dict)

    if package_name is None:
        return None

    return [*base_path.glob(package_name), *base_path.glob(f"{package_name}.py")]


def get_project_modules_from_toml(toml_dict: TomlDict) -> List[str]:
    """Get the project name from a project file.

    The following files are checked in order:
        - pyproject.toml
    """
    package_name = get_package_paths_from_toml(toml_dict)

    if package_name is None:
        raise TomlValueMissingError('Failed to get package from config files.')

    return [str(p) for p in package_name]


T = TypeVar('T')


def first_not_none(candidates: Iterable[Optional[T]]) -> Optional[T]:
    """Get the first of an iterable which is not None.

    Returns None if the search fails.
    """
    for candidate in candidates:
        if candidate is not None:
            return candidate

    return None


def get_config_file(*, base_path: Optional[Path] = None) -> TomlDict:
    """Find the config file and load it as a TomlDict.

    Files are searched for backwards from the current working directory.
    Candidates are described in `candidate_filenames`.
    """
    candidate_filenames = (
        'summon.toml',
        'pyproject.toml',
    )

    base_path = base_path if base_path is not None else Path.cwd()

    config_file_candidates = (
        reverse_directory_search(candidate, base_path)
        for candidate in candidate_filenames
    )

    toml_file = first_not_none(config_file_candidates)

    if toml_file is None:
        raise ProjectFileMissingError(
            'Could not find a config file. '
            f'Candidates are: {", ".join(candidate_filenames)}.'
        )

    return toml.load(toml_file)


def get_test_modules(toml_dict: Optional[TomlDict] = None) -> List[str]:
    """Get the test modules from the vigent config file.

    If no modules are specified, the project modules are considered test modules.
    """
    toml_dict = get_config_file() if toml_dict is None else toml_dict

    test_modules_from_config = read_toml_variable(
        toml_dict, ['tool', 'summon', 'plugins', 'python', 'test-modules']
    )

    if is_list_str(test_modules_from_config):
        return test_modules_from_config

    return get_project_modules_from_toml(get_config_file())


def get_project_modules() -> List[str]:
    """Get the project modules from the vigent config file."""
    return get_project_modules_from_toml(get_config_file())


def args_or_all_modules(args: Optional[List[str]]) -> List[str]:
    """Return either the args that were passed in or all modules.

    If `args` is None or empty, the module list will be loaded from the config file.
    """
    if args:
        return args

    toml_dict = get_config_file()

    return sorted(
        {
            *get_project_modules_from_toml(toml_dict),
            *get_extra_modules_from_toml(toml_dict),
            *get_test_modules(toml_dict),
        }
    )

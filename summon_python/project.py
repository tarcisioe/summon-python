"""Functions for getting Python-project related information."""
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
    """Read the project name from Poetry, given the pyproject.toml convention."""
    package_name = read_toml_variable(toml_dict, ['tool', 'poetry', 'name'])

    if package_name is not None and not isinstance(package_name, str):
        raise TomlValueTypeError()

    return package_name


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


def get_project_modules_from_toml(toml_dict: TomlDict) -> List[str]:
    """Get the project name from a project file.

    The following files are checked in order:
        - pyproject.toml
    """
    package_name = read_package_name_from_poetry(toml_dict)

    if package_name is None:
        raise TomlValueMissingError('Failed to get package from config files.')

    return [package_name]


T = TypeVar('T')


def first_not_none(candidates: Iterable[Optional[T]]) -> Optional[T]:
    """Get the first of an iterable which is not None.

    Returns None if the search fails.
    """
    for candidate in candidates:
        if candidate is not None:
            return candidate

    return None


def get_config_file() -> TomlDict:
    """Find the config file and load it as a TomlDict.

    Files are searched for backwards from the current working directory.
    Candidates are described in `candidate_filenames`.
    """
    candidate_filenames = (
        'summon.toml',
        'pyproject.toml',
    )

    config_file_candidates = (
        reverse_directory_search(candidate, Path.cwd())
        for candidate in candidate_filenames
    )

    toml_file = first_not_none(config_file_candidates)

    if toml_file is None:
        raise ProjectFileMissingError(
            'Could not find a config file. '
            f'Candidates are: {", ".join(candidate_filenames)}.'
        )

    return toml.load(toml_file)


def get_test_modules() -> List[str]:
    """Get the test modules from the vigent config file.

    If no modules are specified, the project modules are considered test modules.
    """
    config_file = get_config_file()

    test_modules_from_config = read_toml_variable(
        config_file, ['tool', 'summon', 'plugins', 'python', 'test-modules']
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

    return [
        *get_project_modules_from_toml(toml_dict),
        *get_extra_modules_from_toml(toml_dict),
    ]

from pathlib import Path

from summon_python.project import (
    get_config_file,
    get_package_paths_from_toml,
)


def test_get_single_file_package_paths(datadir: Path) -> None:
    project_dir = datadir / 'single_file'

    toml_dict = get_config_file(base_path=project_dir)

    paths = get_package_paths_from_toml(toml_dict, base_path=project_dir)

    assert paths == [project_dir / "single_file.py"]


def test_get_package_project_package_paths(datadir: Path) -> None:
    project_dir = datadir / 'package_project'

    toml_dict = get_config_file(base_path=project_dir)

    paths = get_package_paths_from_toml(toml_dict, base_path=project_dir)

    assert paths == [project_dir / "package_project"]

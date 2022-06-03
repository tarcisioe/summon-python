"""Module to manipulate Github Actions config."""
from pathlib import Path
from typing import Any, Dict, List

from ruamel.yaml import safe_dump, safe_load

YamlDict = Dict[str, Any]
RepoList = List[YamlDict]


def get_pre_commit_config_yml() -> RepoList:
    """Generate the .pre-commit-config.yml contents."""

    return [
        {
            'repo': 'https://github.com/pre-commit/pre-commit-hooks',
            'rev': 'v4.2.0',
            'hooks': [
                {'id': 'check-yaml'},
                {'id': 'end-of-file-fixer'},
                {'id': 'trailing-whitespace'},
            ],
        },
        {
            'repo': 'local',
            'hooks': [
                {
                    'id': 'linters',
                    'name': 'Lint',
                    'entry': 'poetry run summon lint --no-full-report',
                    'language': 'system',
                    'types': ['python'],
                    'require_serial': True,
                },
                {
                    'id': 'formatters',
                    'name': 'Format',
                    'entry': 'poetry run summon format',
                    'language': 'system',
                    'types': ['python'],
                },
            ],
        },
    ]


def read_current_pre_commit_hooks(project_base: Path) -> YamlDict:
    """Read the pre-commit hooks from a given project.

    Args:
        project_base: The base directory of the project.
    """

    file_path = project_base / '.pre-commit-config.yaml'

    if not file_path.is_file():
        return {}

    with file_path.open() as yaml_file:
        return safe_load(yaml_file)


def setup_pre_commit_hooks_yml(project_base: Path) -> None:
    """Setup a .pre-commit-config.yml configuration for a Python project.

    Args:
        project_base: The base directory of the project, where
                      .pre-commit-config will be located.
    """

    current = read_current_pre_commit_hooks(project_base)

    repos: RepoList = current.get('repos', [])
    repos_to_add = get_pre_commit_config_yml()

    all_repos = {repo['repo']: repo for repo in (*repos, *repos_to_add)}

    with (project_base / '.pre-commit-config.yaml').open('w') as yaml_file:
        safe_dump({'repos': list(all_repos.values())}, yaml_file)

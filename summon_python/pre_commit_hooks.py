"""Module to manipulate Github Actions config."""
from pathlib import Path
from textwrap import dedent


def get_pre_commit_config_yml() -> str:
    """Generate the .pre-commit-config.yml contents."""
    return dedent(
        '''\
        # vim: set ft=yaml ts=2 sw=2:
        repos:
        - repo: https://github.com/pre-commit/pre-commit-hooks
          rev: v4.2.0
          hooks:
          - id: check-yaml
          - id: end-of-file-fixer
          - id: trailing-whitespace
        - repo: local
          hooks:
          - id: linters
            name: Lint
            entry: poetry run summon lint --no-full-report
            language: system
            types: [python]
            require_serial: true
          - id: formatters
            name: Format
            entry: poetry run summon format
            language: system
            types: [python]
        '''
    )


def setup_pre_commit_hooks_yml(project_base: Path) -> None:
    """Setup a .pre-commit-config.yml configuration for a Python project.

    Args:
        project_base: The base directory of the project, where
                      .pre-commit-config will be located.
    """

    (project_base / '.pre-commit-config.yaml').write_text(get_pre_commit_config_yml())

"""Summon plugin for Python projects."""
import sys
from textwrap import dedent
from typing import List, Optional
from pathlib import Path

import typer
from summon.exec import Result, check_commands, execute
from summon.plugins import hookimpl
from summon.tasks import task
from summon.project import reverse_directory_search

from .project import args_or_all_modules, get_project_modules, get_test_modules


@hookimpl
def register_tasks() -> None:
    """Register tasks related to Python projects."""

    def test(
        coverage: bool = typer.Option(  # noqa: B008
            default=False, help='Generate coverage information.'
        ),
        html: bool = typer.Option(  # noqa: B008
            default=False, help='Generate an html coverage report.'
        ),
    ) -> List[Result]:
        """Run tests."""
        coverage_flag = [f'--cov={",".join(get_project_modules())}'] if coverage else []

        test_modules = get_test_modules()

        return [
            execute(['pytest', *coverage_flag, *test_modules], raise_error=False),
            *(coverage_html() if coverage and html else ()),
        ]

    task(check_commands(test))

    def lint(
        files: Optional[List[str]] = typer.Argument(default=None),  # noqa: B008
        *,
        full_report: bool = typer.Option(  # noqa: B008
            default=False, help='Print detailed reports.'
        ),
    ) -> List[Result]:
        """Run all linters.

        If files is omitted. everything is linted.
        """

        subject = args_or_all_modules(files)

        if not subject:
            return []

        pylint_reports = ['-r', 'y'] if full_report else ['-r', 'n']

        return [
            execute(['mypy', *subject], raise_error=False),
            execute(['flake8', *subject], raise_error=False),
            execute(
                ['pylint', *pylint_reports, *subject],
                raise_error=False,
            ),
        ]

    task(check_commands(lint))

    def format(  # pylint: disable=redefined-builtin
        files: Optional[List[str]] = typer.Argument(default=None),  # noqa: B008
        check: bool = typer.Option(  # noqa: B008
            default=False, help='Only checks instead of modifying.'
        ),
    ) -> List[Result]:
        """Run all formatters.

        If files is omitted. everything is linted.
        """

        check_flag = ['--check'] if check else []

        subject = args_or_all_modules(files)

        if not subject:
            return []

        args = ['-q', *check_flag, *subject]

        return [
            execute(['black', *args], raise_error=False),
            execute(['isort', *args], raise_error=False),
        ]

    task(check_commands(format))

    def coverage_html():
        """Generate an html coverage report."""
        return [
            execute('coverage html', raise_error=False),
        ]

    task(check_commands(coverage_html))

    def static_checks() -> List[Result]:
        """Run all static checks over all code."""
        return [
            *lint([]),
            *format([], check=True),
        ]

    task(check_commands(static_checks))

    def all_checks() -> List[Result]:
        """Run all checks (static checks and tests) over all code."""
        return [
            *static_checks(),
            *test(),
        ]

    task(check_commands(all_checks))

    @task
    def setup() -> None:
        """Setup sane defaults for a python project."""
        pyproject_path = reverse_directory_search('pyproject.toml', Path.cwd())

        if pyproject_path is None:
            print('Could not find a pyproject.toml file. Aborting.', file=sys.stderr)
            return

        base_directory = pyproject_path.parent

        setup_github_actions(base_directory)


def setup_github_actions(project_base: Path) -> None:
    """Setup a summon.yml Github Actions configuration for a python project.

    Args:
        project_base: The base directory of the project, where .github will be located.
    """

    workflows = project_base / '.github/workflows'

    workflows.mkdir(parents=True, exist_ok=True)

    (workflows / 'summon.yml').write_text(dedent('''\
        # vim: set ft=yaml ts=2 sw=2:

        name: Summon Tasks

        on: [push]

        jobs:
          lint:
            strategy:
              matrix:
                python: ['3.10']
                os: [ubuntu-latest]

            name: Static checks

            runs-on: ${{ matrix.os }}

            steps:
              - uses: actions/checkout@v2

              - name: Set up Python ${{ matrix.python }}
                uses: actions/setup-python@v1
                with:
                  python-version: ${{ matrix.python }}

              - name: Install dependencies
                run: |
                  python -m pip install --upgrade pip
                  pip install poetry
                  poetry install

              - name: Run static checks
                run: poetry run summon static-checks


          test:
            strategy:
              matrix:
                python: ['3.10']
                os: [ubuntu-latest, windows-latest]

            name: Python ${{ matrix.python }} on ${{ matrix.os }}

            runs-on: ${{ matrix.os }}

            steps:
              - uses: actions/checkout@v2

              - name: Set up Python ${{ matrix.python }}
                uses: actions/setup-python@v1
                with:
                  python-version: ${{ matrix.python }}

              - name: Install dependencies
                run: |
                  python -m pip install --upgrade pip
                  pip install poetry
                  poetry install

              - name: Run tests
                run: poetry run summon test --coverage

              - name: Generate coverage.xml
                run: poetry run coverage xml

              - uses: codecov/codecov-action@v1
                with:
                  fail_ci_if_error: false  # Setting this to true is a headache.
    '''))

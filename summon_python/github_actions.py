"""Module to manipulate Github Actions config."""
from textwrap import dedent
from pathlib import Path


def get_github_actions_yml() -> str:
    """Generate the Github Actions yml."""
    return dedent(
        '''\
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
    ''')


def setup_github_actions(project_base: Path) -> None:
    """Setup a summon.yml Github Actions configuration for a python project.

    Args:
        project_base: The base directory of the project, where .github will be located.
    """

    workflows = project_base / '.github/workflows'

    workflows.mkdir(parents=True, exist_ok=True)

    (workflows / 'summon.yml').write_text(get_github_actions_yml())

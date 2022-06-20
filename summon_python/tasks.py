"""Definition of tasks to be registered by the plugin."""
from typing import List, Optional

import typer
from summon.execute import execute, Result
from summon.tasks import task_with_result, task_with_results

from .project import args_or_all_modules, get_project_modules, get_test_modules


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
        execute(['pytest', *coverage_flag, *test_modules]),
        *([coverage_html()] if coverage and html else ()),
    ]


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

    pylint_report_flag = 'y' if full_report else 'n'

    return [
        execute(['mypy', *subject], raise_error=False),
        execute(['flake8', *subject], raise_error=False),
        execute(
            ['pylint', '-r', pylint_report_flag, *subject],
            raise_error=False,
        ),
    ]


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


def coverage_html() -> Result:
    """Generate an html coverage report."""
    return execute('coverage html', raise_error=False)


def static_checks() -> List[Result]:
    """Run all static checks over all code."""
    return [
        *lint([]),
        *format([], check=True),
    ]


def all_checks() -> List[Result]:
    """Run all checks (static checks and tests) over all code."""
    return [
        *static_checks(),
        *test(),
    ]


def register_tasks() -> None:
    """Register tasks related to Python projects."""

    task_with_results(all_checks)
    task_with_result(coverage_html)
    task_with_results(format)
    task_with_results(lint)
    task_with_results(static_checks)
    task_with_results(test)

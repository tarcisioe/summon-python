"""Summon plugin for Python projects."""
from summon.plugins import hookimpl

from .tasks import register_tasks


hookimpl(register_tasks)

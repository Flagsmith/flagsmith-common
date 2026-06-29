"""Composite startup verbs for the `flagsmith` entrypoint.

These mirror the sequencing that Core API's `run-docker.sh` performed in
shell, but run in a single process so the Django boot cost is paid once.
"""

import os
import shlex

from django.conf import settings
from django.core.management import (
    execute_from_command_line as django_execute_from_command_line,
)

WAIT_FOR_MIGRATIONS_TIMEOUT_SECONDS = 30


def _wait_for_db(
    *,
    wait_for_migrations: bool = False,
    database: str = "default",
    wait_for: int | None = None,
) -> None:
    if os.environ.get("SKIP_WAIT_FOR_DB"):
        return
    args = ["waitfordb", "--database", database]
    if wait_for is not None:
        args += ["--waitfor", str(wait_for)]
    if wait_for_migrations:
        args.append("--migrations")
    django_execute_from_command_line(["flagsmith", *args])


def _migrate() -> None:
    _wait_for_db()
    databases: list[str] = getattr(settings, "FLAGSMITH_MIGRATE_DATABASES", ["default"])
    for database in databases:
        django_execute_from_command_line(
            ["flagsmith", "migrate", "--database", database]
        )
    django_execute_from_command_line(["flagsmith", "createcachetable"])


def migrate(argv: list[str], *, prog: str) -> None:
    """Migrate the configured databases, then create the cache table."""
    if argv:
        django_execute_from_command_line(["flagsmith", "migrate", *argv])
        return
    _migrate()


def serve(argv: list[str], *, prog: str) -> None:
    """Wait for the database, then start the API server."""
    _wait_for_db()
    django_execute_from_command_line(["flagsmith", "start", "api", *argv])


def run_task_processor(argv: list[str], *, prog: str) -> None:
    """Migrate, wait for migrations to be applied, then start the task processor."""
    _migrate()
    databases: list[str] = getattr(
        settings, "FLAGSMITH_WAIT_FOR_MIGRATIONS_DATABASES", ["default"]
    )
    for database in databases:
        _wait_for_db(
            wait_for_migrations=True,
            database=database,
            wait_for=WAIT_FOR_MIGRATIONS_TIMEOUT_SECONDS,
        )
    django_execute_from_command_line(["flagsmith", "start", "task-processor", *argv])


def migrate_and_serve(argv: list[str], *, prog: str) -> None:
    """Migrate, run any configured startup commands, then start the API server."""
    _migrate()
    startup_commands: list[str] = getattr(settings, "FLAGSMITH_STARTUP_COMMANDS", [])
    for command in startup_commands:
        django_execute_from_command_line(["flagsmith", *shlex.split(command)])
    django_execute_from_command_line(["flagsmith", "start", "api", *argv])

import subprocess
from operator import itemgetter
from pathlib import Path
from typing import Any, Callable

import prometheus_client
from django.apps import apps
from django.core.management import BaseCommand, CommandParser
from django.template.loader import get_template
from django.utils.module_loading import autodiscover_modules
from prometheus_client.metrics import MetricWrapperBase

from common.core.docgen.events import (
    EventEntry,
    get_event_entries_from_tree,
    merge_event_entries,
)


class Command(BaseCommand):
    help = "Generate documentation for the Flagsmith codebase."

    def add_arguments(self, parser: CommandParser) -> None:
        subparsers = parser.add_subparsers(
            title="sub-commands",
            required=True,
        )

        metric_parser = subparsers.add_parser(
            "metrics",
            help="Generate metrics documentation.",
        )
        metric_parser.set_defaults(handle_method=self.handle_metrics)

        events_parser = subparsers.add_parser(
            "events",
            help="Generate structlog events documentation.",
        )
        events_parser.set_defaults(handle_method=self.handle_events)

    def initialise(self) -> None:
        from common.gunicorn import metrics  # noqa: F401

        autodiscover_modules(
            "metrics",
        )

    def handle(
        self,
        *args: Any,
        handle_method: Callable[..., None],
        **options: Any,
    ) -> None:
        self.initialise()
        handle_method(*args, **options)

    def handle_metrics(self, *args: Any, **options: Any) -> None:
        template = get_template("docgen-metrics.md")

        flagsmith_metrics = sorted(
            (
                {
                    "name": collector._name,
                    "documentation": collector._documentation,
                    "labels": collector._labelnames,
                    "type": collector._type,
                }
                for collector in prometheus_client.REGISTRY._collector_to_names
                if isinstance(collector, MetricWrapperBase)
            ),
            key=itemgetter("name"),
        )

        self.stdout.write(
            template.render(
                context={"flagsmith_metrics": flagsmith_metrics},
            )
        )

    def handle_events(self, *args: Any, **options: Any) -> None:
        template = get_template("docgen-events.md")

        repo_root = _get_repo_root()
        entries: list[EventEntry] = []
        for app_config in apps.get_app_configs():
            entries.extend(
                get_event_entries_from_tree(
                    Path(app_config.path),
                    app_label=app_config.label,
                    module_prefix=app_config.name,
                )
            )
        merged = merge_event_entries(entries)

        flagsmith_events = [
            {
                "name": entry.name,
                "level": entry.level,
                "locations": [
                    {
                        "path": _relative_if_under(location.path, repo_root),
                        "line": location.line,
                    }
                    for location in entry.locations
                ],
                "attributes": sorted(entry.attributes),
            }
            for entry in merged
        ]

        self.stdout.write(
            template.render(
                context={"flagsmith_events": flagsmith_events},
            )
        )


def _get_repo_root() -> Path:
    """Resolve the git repo root for emitted source paths.

    Falls back to the current working directory when git isn't available or
    the CWD isn't inside a repo.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()
    return Path(result.stdout.strip())


def _relative_if_under(path: Path, base: Path) -> Path:
    try:
        return path.relative_to(base)
    except ValueError:
        return path

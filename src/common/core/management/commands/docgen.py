from operator import itemgetter
from typing import Any, Callable

import prometheus_client
from django.core.management import BaseCommand, CommandParser
from django.template.loader import get_template
from django.utils.module_loading import autodiscover_modules
from prometheus_client.metrics import MetricWrapperBase


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

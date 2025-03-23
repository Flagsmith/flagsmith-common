from typing import Any, Callable

from django.core.management import BaseCommand, CommandParser
from django.utils.module_loading import autodiscover_modules

from common.gunicorn.utils import add_arguments, run_server


class Command(BaseCommand):
    help = "Start the Flagsmith application."

    def create_parser(self, *args: Any, **kwargs: Any) -> CommandParser:
        return super().create_parser(*args, conflict_handler="resolve", **kwargs)

    def add_arguments(self, parser: CommandParser) -> None:
        gunicorn_parser = parser.add_argument_group("gunicorn")

        add_arguments(gunicorn_parser)

        subparsers = parser.add_subparsers(
            title="sub-commands",
            required=True,
        )
        api_parser = subparsers.add_parser(
            "api",
            help="Start the Core API.",
        )
        api_parser.set_defaults(handle_method=self.handle_api)

    def initialise(self) -> None:
        autodiscover_modules("metrics")

    def handle(
        self,
        *args: Any,
        handle_method: Callable[..., None],
        **options: Any,
    ) -> None:
        self.initialise()
        handle_method(*args, **options)

    def handle_api(self, *args: Any, **options: Any) -> None:
        run_server(options)

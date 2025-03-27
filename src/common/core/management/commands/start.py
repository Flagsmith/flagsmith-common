from typing import Any, Callable

from django.core.management import BaseCommand, CommandParser
from django.utils.module_loading import autodiscover_modules

from common.gunicorn.utils import add_arguments as add_gunicorn_arguments
from common.gunicorn.utils import run_server
from task_processor.utils import add_arguments as add_task_processor_arguments
from task_processor.utils import start_task_processor


class Command(BaseCommand):
    help = "Start the Flagsmith application."

    def create_parser(self, *args: Any, **kwargs: Any) -> CommandParser:
        return super().create_parser(*args, conflict_handler="resolve", **kwargs)

    def add_arguments(self, parser: CommandParser) -> None:
        add_gunicorn_arguments(parser)

        subparsers = parser.add_subparsers(
            title="sub-commands",
            required=True,
        )

        api_parser = subparsers.add_parser(
            "api",
            help="Start the Core API.",
        )
        api_parser.set_defaults(handle_method=self.handle_api)

        task_processor_parser = subparsers.add_parser(
            "task-processor",
            help="Start the Task Processor.",
        )
        task_processor_parser.set_defaults(handle_method=self.handle_task_processor)
        add_task_processor_arguments(task_processor_parser)

    def initialise(self) -> None:
        autodiscover_modules(
            "metrics",
            "tasks",
        )

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

    def handle_task_processor(self, *args: Any, **options: Any) -> None:
        with start_task_processor(options):
            # Delegate signal handling to Gunicorn.
            # The task processor will finalise once Gunicorn is shut down.
            run_server(options)

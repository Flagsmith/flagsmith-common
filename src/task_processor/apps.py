from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from health_check.plugins import plugin_dir  # type: ignore[import-untyped]

from task_processor.task_run_method import TaskRunMethod


class TaskProcessorAppConfig(AppConfig):
    name = "task_processor"

    def ready(self) -> None:
        if settings.TASK_RUN_METHOD != TaskRunMethod.TASK_PROCESSOR:
            return

        self._validate_database_settings()
        self._register_health_check()

    def _register_health_check(self) -> None:
        """
        Register the health check for the task processor
        """
        if not settings.ENABLE_TASK_PROCESSOR_HEALTH_CHECK:
            return

        from .health import TaskProcessorHealthCheckBackend

        plugin_dir.register(TaskProcessorHealthCheckBackend)

    def _validate_database_settings(self) -> None:
        """
        Validate that multi-database is setup correctly
        """
        if "task_processor" not in settings.TASK_PROCESSOR_DATABASES:
            return  # Not using a separate database

        if "task_processor" not in settings.DATABASES:
            raise ImproperlyConfigured(
                "DATABASES must include 'task_processor' when using a separate task processor database."
            )

        router_name = "task_processor.routers.TaskProcessorRouter"
        if router_name not in settings.DATABASE_ROUTERS:
            raise ImproperlyConfigured(
                "DATABASE_ROUTERS must include 'task_processor.routers.TaskProcessorRouter' "
                "when using a separate task processor database."
            )

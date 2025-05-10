from django.conf import settings
from django.db.models import Model


class TaskProcessorRouter:
    """
    Routing of database operations for task processor models
    """

    route_app_labels = ["task_processor"]

    @property
    def is_enabled(self) -> bool:
        return "task_processor" in settings.TASK_PROCESSOR_DATABASES

    def db_for_read(self, model: type[Model], **hints: None) -> str | None:
        """
        If enabled, route "task_processor" models to the a se database
        """
        if not self.is_enabled:
            return None

        if model._meta.app_label in self.route_app_labels:
            return "task_processor"

        return None

    def db_for_write(self, model: type[Model], **hints: None) -> str | None:
        """
        Attempts to write task processor models go to 'task_processor' database.
        """
        if not self.is_enabled:
            return None

        if model._meta.app_label in self.route_app_labels:
            return "task_processor"

        return None

    def allow_relation(self, obj1: Model, obj2: Model, **hints: None) -> bool | None:
        """
        Relations between objects are allowed if both objects are
        in the task processor database.
        """
        if not self.is_enabled:
            return None

        both_objects_from_task_processor = (
            obj1._meta.app_label in self.route_app_labels
            and obj2._meta.app_label in self.route_app_labels
        )

        if both_objects_from_task_processor:
            return True

        return None

    def allow_migrate(
        self,
        db: str,
        app_label: str,
        **hints: None,
    ) -> bool | None:
        """
        Allow migrations for task processor models to run in both databases

        NOTE: Even if, from a fresh install, the task processor tables are not
        required in both databases, this is required to allow for easier
        transition between a single database and a multi-database setup.
        """
        if not self.is_enabled:
            return None

        if app_label in self.route_app_labels:
            return db in ["default", "task_processor"]

        return None

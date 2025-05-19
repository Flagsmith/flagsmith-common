from django.db.models import Model


class TaskProcessorRouter:
    """
    Routing of database operations for task processor models
    """

    route_app_labels = ["task_processor"]

    def db_for_read(self, model: type[Model], **hints: None) -> str | None:
        if model._meta.app_label in self.route_app_labels:
            return "task_processor"

        return None

    def db_for_write(self, model: type[Model], **hints: None) -> str | None:
        if model._meta.app_label in self.route_app_labels:
            return "task_processor"

        return None

    def allow_relation(self, obj1: Model, obj2: Model, **hints: None) -> bool | None:
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
        Allow migrations to hit BOTH databases

        NOTE: We run migrations on both databases because:

        - The `task_processor` separate database was only introduced later in
          history, and migrating to it does not delete old data from `default`.
          We'd rather keep data in `default` consistent across time rather than
          leaving behind possibly inconsistent data.
        - We want to make it easier to migrate to the new database, _or back_
          to a single database setup if needed. Running DDL consistently helps.
        """
        if app_label in self.route_app_labels:
            return db in ["default", "task_processor"]

        return None

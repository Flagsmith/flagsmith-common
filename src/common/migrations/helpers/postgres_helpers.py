from contextlib import suppress

from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import ProjectState


class PostgresOnlyRunSQL(migrations.RunSQL):
    @classmethod
    def from_sql_file(
        cls,
        file_path: str,
        reverse_sql: str = "",
    ) -> "PostgresOnlyRunSQL":
        with open(file_path) as forward_sql:
            with suppress(FileNotFoundError):
                with open(reverse_sql) as reverse_sql_file:
                    reverse_sql = reverse_sql_file.read()
            return cls(forward_sql.read(), reverse_sql=reverse_sql)

    def database_forwards(
        self,
        app_label: str,
        schema_editor: BaseDatabaseSchemaEditor,
        from_state: ProjectState,
        to_state: ProjectState,
    ) -> None:
        if schema_editor.connection.vendor != "postgresql":
            return
        super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(
        self,
        app_label: str,
        schema_editor: BaseDatabaseSchemaEditor,
        from_state: ProjectState,
        to_state: ProjectState,
    ) -> None:
        if schema_editor.connection.vendor != "postgresql":
            return
        super().database_backwards(app_label, schema_editor, from_state, to_state)

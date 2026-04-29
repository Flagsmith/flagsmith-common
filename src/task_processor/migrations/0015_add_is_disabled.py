import os

from django.db import migrations, models

from common.migrations.helpers import PostgresOnlyRunSQL


class Migration(migrations.Migration):

    dependencies = [
        ("task_processor", "0014_add_trace_context"),
    ]

    operations = [
        migrations.AddField(
            model_name="recurringtask",
            name="is_disabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="recurringtask",
            name="num_consecutive_failures",
            field=models.IntegerField(default=0),
        ),
        PostgresOnlyRunSQL.from_sql_file(
            os.path.join(
                os.path.dirname(__file__),
                "sql",
                "0015_get_recurringtasks_to_process.sql",
            ),
            reverse_sql=os.path.join(
                os.path.dirname(__file__),
                "sql",
                "0013_get_recurringtasks_to_process.sql",
            ),
        ),
    ]

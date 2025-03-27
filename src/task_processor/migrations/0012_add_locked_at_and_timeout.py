# Generated by Django 3.2.23 on 2025-01-06 04:51

import datetime
from django.db import migrations, models
import os

from common.migrations.helpers import PostgresOnlyRunSQL


class Migration(migrations.Migration):

    dependencies = [
        ("task_processor", "0011_add_priority_to_get_tasks_to_process"),
    ]

    operations = [
        migrations.AddField(
            model_name="recurringtask",
            name="locked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="recurringtask",
            name="timeout",
            field=models.DurationField(default=datetime.timedelta(minutes=30)),
        ),
        migrations.AddField(
            model_name="task",
            name="timeout",
            field=models.DurationField(blank=True, null=True),
        ),
        PostgresOnlyRunSQL.from_sql_file(
            os.path.join(
                os.path.dirname(__file__),
                "sql",
                "0012_get_recurringtasks_to_process.sql",
            ),
            reverse_sql="DROP FUNCTION IF EXISTS get_recurringtasks_to_process()",
        ),
    ]

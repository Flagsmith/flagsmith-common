# Generated by Django 3.2.20 on 2023-10-13 04:44

from django.db import migrations

from common.migrations.helpers import PostgresOnlyRunSQL
import os


class Migration(migrations.Migration):
    dependencies = [
        ("task_processor", "0010_task_priority"),
    ]

    operations = [
        PostgresOnlyRunSQL.from_sql_file(
            os.path.join(
                os.path.dirname(__file__),
                "sql",
                "0011_get_tasks_to_process.sql",
            ),
            reverse_sql=os.path.join(
                os.path.dirname(__file__),
                "sql",
                "0008_get_tasks_to_process.sql",
            ),
        ),
    ]

# Generated by Django 3.2.15 on 2022-10-07 09:53

from django.db import migrations, models

from common.migrations.helpers import PostgresOnlyRunSQL


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("task_processor", "0003_add_completed_to_task"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterIndexTogether(
                    name="task",
                    index_together=set(),
                ),
                migrations.AddIndex(
                    model_name="task",
                    index=models.Index(
                        condition=models.Q(("completed", False)),
                        fields=["num_failures", "scheduled_for"],
                        name="incomplete_tasks_idx",
                    ),
                ),
            ],
            database_operations=[
                PostgresOnlyRunSQL(
                    "DROP INDEX CONCURRENTLY task_processor_task_scheduled_for_num_failur_17d6dc77_idx;",
                    reverse_sql='CREATE INDEX "task_processor_task_scheduled_for_num_failur_17d6dc77_idx" ON "task_processor_task" ("scheduled_for", "num_failures", "completed");',
                ),
                PostgresOnlyRunSQL(
                    'CREATE INDEX CONCURRENTLY "incomplete_tasks_idx" ON "task_processor_task" ("num_failures", "scheduled_for") WHERE NOT "completed";',
                    reverse_sql='DROP INDEX CONCURRENTLY "incomplete_tasks_idx";',
                ),
            ],
        ),
    ]

# Generated by Django 4.2.7 on 2023-11-11 05:50

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("App", "0006_bookmarkfile_tasks_alter_scrapyresponselog_html_file"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bookmarkfile",
            name="tasks",
            field=models.JSONField(default=list),
        ),
    ]

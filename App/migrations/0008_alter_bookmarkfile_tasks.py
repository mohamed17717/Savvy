# Generated by Django 4.2.7 on 2023-11-11 08:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0007_alter_bookmarkfile_tasks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookmarkfile',
            name='tasks',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
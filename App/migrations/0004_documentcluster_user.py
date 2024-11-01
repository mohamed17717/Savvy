# Generated by Django 4.2.6 on 2023-10-17 08:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("App", "0003_alter_bookmarkfile_location"),
    ]

    operations = [
        migrations.AddField(
            model_name="documentcluster",
            name="user",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="clusters",
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
    ]

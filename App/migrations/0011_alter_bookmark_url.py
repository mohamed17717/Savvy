# Generated by Django 4.2.7 on 2023-12-04 13:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("App", "0010_alter_bookmark_title"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bookmark",
            name="url",
            field=models.URLField(max_length=2048),
        ),
    ]

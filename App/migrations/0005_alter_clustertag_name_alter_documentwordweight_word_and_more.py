# Generated by Django 4.2.6 on 2023-10-18 23:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("App", "0004_documentcluster_user"),
    ]

    operations = [
        migrations.AlterField(
            model_name="clustertag",
            name="name",
            field=models.CharField(max_length=2048),
        ),
        migrations.AlterField(
            model_name="documentwordweight",
            name="word",
            field=models.CharField(max_length=2048),
        ),
        migrations.AlterField(
            model_name="webpagemetatag",
            name="name",
            field=models.CharField(default="undefined", max_length=2048),
        ),
    ]

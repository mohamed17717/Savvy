# Generated by Django 4.2.7 on 2024-05-07 05:30

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("App", "0037_merge_20240507_0530"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="similaritymatrix",
            name="user",
        ),
        migrations.DeleteModel(
            name="Cluster",
        ),
        migrations.DeleteModel(
            name="SimilarityMatrix",
        ),
    ]

# Generated by Django 4.2.7 on 2024-04-12 15:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("App", "0031_similaritymatrix_bookmarks_ids"),
    ]

    operations = [
        migrations.AddField(
            model_name="cluster",
            name="tags",
            field=models.ManyToManyField(related_name="clusters", to="App.tag"),
        ),
        migrations.AlterField(
            model_name="similaritymatrix",
            name="bookmarks_ids",
            field=models.JSONField(blank=True, default=list),
        ),
    ]

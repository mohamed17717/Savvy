# Generated by Django 4.2.7 on 2024-06-17 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0045_bookmark_app_bookmar_search__40979f_gin'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='bookmarks_count',
            field=models.PositiveSmallIntegerField(db_index=True, default=0),
        ),
    ]

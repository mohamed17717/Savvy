# Generated by Django 4.2.7 on 2024-04-02 06:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0029_remove_bookmark_cloned_remove_bookmark_crawled_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cluster',
            name='bookmarks_count',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='process_status',
            field=models.PositiveSmallIntegerField(choices=[(None, None), (10, 'created'), (20, 'cloned from another user bookmark (to status 60)'), (30, 'sent to scrapy crawler'), (35, 'crawled failed for any reason'), (40, 'crawled succeeded'), (50, 'start text processing'), (60, 'text processed'), (70, 'start clustering process'), (80, 'done the whole flow')], default=10),
        ),
    ]

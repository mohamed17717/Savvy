# Generated by Django 4.2.9 on 2024-01-26 16:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0018_remove_bookmarkfile_tasks_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookmark',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='bookmarks/images/'),
        ),
    ]

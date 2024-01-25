# Generated by Django 4.2.9 on 2024-01-25 02:06

import common.utils.model_utils
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0017_documentcluster_correlation'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bookmarkfile',
            name='tasks',
        ),
        migrations.AlterField(
            model_name='bookmarkfile',
            name='file_hash',
            field=models.CharField(blank=True, editable=False, max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='bookmarkfile',
            name='location',
            field=models.FileField(editable=False, upload_to='users/bookmarks/', validators=[django.core.validators.FileExtensionValidator(['html', 'json']), common.utils.model_utils.FileSizeValidator(5)]),
        ),
    ]

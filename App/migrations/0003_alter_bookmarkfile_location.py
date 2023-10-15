# Generated by Django 4.2.6 on 2023-10-15 20:56

import common.utils.model_utils
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0002_webpageheader_cleaned_text_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookmarkfile',
            name='location',
            field=models.FileField(upload_to='users/bookmarks/', validators=[django.core.validators.FileExtensionValidator(['html', 'json']), common.utils.model_utils.FileSizeValidator(5)]),
        ),
    ]

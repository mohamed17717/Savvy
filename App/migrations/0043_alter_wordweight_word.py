# Generated by Django 4.2.7 on 2024-06-02 04:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0042_alter_bookmarkfile_location_alter_wordweight_word'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wordweight',
            name='word',
            field=models.CharField(db_index=True, max_length=64),
        ),
    ]
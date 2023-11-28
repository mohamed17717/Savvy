# Generated by Django 4.2.7 on 2023-11-28 14:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('App', '0008_alter_bookmarkfile_tasks'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('alias_name', models.CharField(blank=True, max_length=128, null=True)),
                ('weight', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('bookmarks', models.ManyToManyField(blank=True, related_name='tags', to='App.bookmark')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RenameField(
            model_name='documentwordweight',
            old_name='document',
            new_name='bookmark',
        ),
        migrations.DeleteModel(
            name='ClusterTag',
        ),
    ]
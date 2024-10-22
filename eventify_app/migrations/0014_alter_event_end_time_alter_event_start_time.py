# Generated by Django 5.0.3 on 2024-10-03 19:26

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventify_app', '0013_alter_event_end_time_alter_event_start_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='end_time',
            field=models.TimeField(default=datetime.datetime(2024, 10, 3, 19, 26, 16, 810733, tzinfo=datetime.timezone.utc), help_text='Zadejte čas konce eventu', verbose_name='Čas konce eventu'),
        ),
        migrations.AlterField(
            model_name='event',
            name='start_time',
            field=models.TimeField(default=datetime.datetime(2024, 10, 3, 19, 26, 16, 810386, tzinfo=datetime.timezone.utc), help_text='Zadejte čas začátku eventu', verbose_name='Čas začátku eventu'),
        ),
    ]
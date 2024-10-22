# Generated by Django 5.0.3 on 2024-10-07 10:58

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventify_app', '0016_remove_event_end_time_remove_event_start_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketPurchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='eventify_app.event')),
                ('ticket_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='eventify_app.tickettype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
# Generated by Django 5.0.7 on 2024-08-09 08:02

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat_bot_app', '0005_summariserassistant_alter_chatbotuser_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='accent_color',
            field=models.CharField(default='', max_length=300),
        ),
        migrations.AlterField(
            model_name='chatbotuser',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 8, 9, 8, 2, 17, 373325, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='lead',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 8, 9, 8, 2, 17, 373325, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='request',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 8, 9, 8, 2, 17, 372325, tzinfo=datetime.timezone.utc)),
        ),
    ]

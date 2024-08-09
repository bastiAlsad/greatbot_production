# Generated by Django 5.0.7 on 2024-07-31 18:57

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat_bot_app', '0003_lead_alter_chatbotuser_created_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatbotuser',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 7, 31, 18, 57, 41, 646558, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='lead',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 7, 31, 18, 57, 41, 646558, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='request',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 7, 31, 18, 57, 41, 646558, tzinfo=datetime.timezone.utc)),
        ),
        migrations.CreateModel(
            name='Themengebiet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('themenbereich', models.CharField(max_length=255)),
                ('amount', models.PositiveIntegerField(default=1)),
                ('created_for', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat_bot_app.customer')),
            ],
        ),
    ]

# Generated by Django 5.2 on 2025-04-16 11:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='comic',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]

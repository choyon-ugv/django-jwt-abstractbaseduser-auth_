# Generated by Django 5.2 on 2025-04-15 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_blog'),
    ]

    operations = [
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('release_date', models.DateField()),
                ('runtime', models.PositiveIntegerField(help_text='Runtime in minutes')),
                ('image', models.ImageField(blank=True, null=True, upload_to='movies/images/')),
                ('description', models.TextField()),
                ('watch_link', models.URLField(blank=True, max_length=255, null=True)),
            ],
        ),
    ]

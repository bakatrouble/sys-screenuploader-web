# Generated by Django 3.0.2 on 2023-10-29 00:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0012_titleentry_custom'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='destinationmoduleconfigdiscord',
            name='uploader',
        ),
    ]

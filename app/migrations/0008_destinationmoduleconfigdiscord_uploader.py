# Generated by Django 3.0.2 on 2020-01-29 00:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_destinationmoduleconfigdiscord'),
    ]

    operations = [
        migrations.AddField(
            model_name='destinationmoduleconfigdiscord',
            name='uploader',
            field=models.CharField(choices=[('gfycat', 'Gfycat'), ('streamable', 'Streamable (blocked in Russia)')], default='streamable', max_length=32),
        ),
    ]
# Generated by Django 3.0.2 on 2020-01-20 23:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_destinationmoduleconfigtelegram_send_as_documents'),
    ]

    operations = [
        migrations.CreateModel(
            name='DestinationModuleConfigDiscord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel_id', models.CharField(max_length=32)),
            ],
            options={
                'verbose_name': 'Destination module config Telegram',
                'verbose_name_plural': 'Destination module config Telegram',
            },
        ),
    ]

# Generated by Django 3.0.2 on 2020-05-01 22:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_uploadedmedia_caption'),
    ]

    operations = [
        migrations.CreateModel(
            name='TitleEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('hash', models.CharField(db_index=True, max_length=32)),
            ],
        ),
    ]

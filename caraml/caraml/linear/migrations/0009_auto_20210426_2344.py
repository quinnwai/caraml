# Generated by Django 3.1.8 on 2021-04-27 04:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('linear', '0008_auto_20210426_2343'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='file',
            field=models.FileField(upload_to='datasets'),
        ),
    ]
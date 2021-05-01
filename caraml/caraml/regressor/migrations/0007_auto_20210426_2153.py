# Generated by Django 3.1.8 on 2021-04-27 02:53

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regressor', '0006_record_features'),
    ]

    operations = [
        migrations.AlterField(
            model_name='record',
            name='features',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), size=None),
        ),
    ]
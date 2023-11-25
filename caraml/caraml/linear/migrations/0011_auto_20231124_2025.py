# Generated by Django 3.1.8 on 2023-11-25 02:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('linear', '0010_auto_20231107_2041'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='record',
            name='numFolds',
        ),
        migrations.RemoveField(
            model_name='record',
            name='result',
        ),
        migrations.AddField(
            model_name='record',
            name='testError',
            field=models.DecimalField(decimal_places=5, default=0.98, max_digits=5),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='record',
            name='trainError',
            field=models.DecimalField(decimal_places=5, default=0.98, max_digits=5),
            preserve_default=False,
        ),
    ]

# Generated by Django 3.1.1 on 2021-04-22 21:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('linear', '0002_auto_20210420_2009'),
    ]

    operations = [
        migrations.CreateModel(
            name='Records',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('dateTime', models.DateTimeField()),
                ('randomState', models.PositiveIntegerField()),
                ('numFolds', models.PositiveIntegerField()),
                ('target', models.CharField(max_length=100)),
                ('result', models.DecimalField(decimal_places=3, max_digits=6)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

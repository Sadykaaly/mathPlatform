# Generated by Django 2.2.6 on 2021-03-08 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_auto_20210306_2103'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quiz',
            name='time_limit',
            field=models.PositiveIntegerField(blank=True, help_text='Time limit from starting of quiz in minutes', null=True, verbose_name='Time limit'),
        ),
    ]

# Generated by Django 3.1.14 on 2022-03-04 06:24

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('graphql_api', '0007_auto_20220304_0615'),
    ]

    operations = [
        migrations.AlterField(
            model_name='table',
            name='name',
            field=models.CharField(db_index=True, help_text='at least 5 chars, at most 128 chars.\nbegin with letter, consist of (letter | digit | underscore).', max_length=128, unique=True, validators=[django.core.validators.RegexValidator('^[a-z][_a-z0-9]{4,}$')]),
        ),
    ]

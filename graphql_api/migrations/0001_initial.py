# Generated by Django 3.1.14 on 2022-03-11 07:46

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import graphql_api.constants.constant


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Table',
            fields=[
                ('urn', models.CharField(max_length=512, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, help_text='\n                                at least 5 chars, at most 128 chars. \n                                begins with letter, consist of (letter | digit | underscore). \n                                regexp validator: ^[a-z][_a-z0-9]{4,}$\n                            ', max_length=128, unique=True, validators=[django.core.validators.RegexValidator('^[a-z][_a-z0-9]{4,}$')])),
                ('alias', models.CharField(max_length=32, null=True, unique=True)),
                ('tags', models.CharField(max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name='Relationship',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('join_type', models.CharField(choices=[('INNER_JOIN', 'inner join'), ('LEFT_JOIN', 'left join'), ('RIGHT_JOIN', 'right join'), ('FULL_JOIN', 'full join')], default=graphql_api.constants.constant.JoinTypes['INNER_JOIN'], max_length=16)),
                ('join_condition', models.TextField(default='{{ l }}.foreign_key = {{ r }}.id')),
                ('left_table_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='left_table_name', to='graphql_api.table')),
                ('right_table_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='right_table_name', to='graphql_api.table')),
            ],
        ),
        migrations.CreateModel(
            name='Column',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('table', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='graphql_api.table')),
            ],
        ),
    ]

import json

from django.core.validators import RegexValidator
from django.db import models

from graphql_api.constants.constant import TableTypes, JoinTypes, TABLE_NAME_REGEXP


class Table(models.Model):
    name = models.CharField(max_length=128, unique=True, db_index=True,
                            validators=(RegexValidator(TABLE_NAME_REGEXP),),
                            help_text=f'''
                            at least 5 chars, at most 128 chars. 
                            begins with letter, consist of (letter | digit | underscore). 
                            regexp validator: {TABLE_NAME_REGEXP}
                            ''')
    alias = models.CharField(max_length=32, unique=True)
    table_type = models.CharField(max_length=32, choices=[
        (table_type.name, table_type.value) for table_type in TableTypes
    ], default=TableTypes.DWD)

    # display columns in list view page.
    def columns(self):
        return [column.name for column in self.column_set.all()]

    def __str__(self):
        return self.name


class Column(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)

    def __str__(self):
        return ''


class Relationship(models.Model):
    left_table_name = models.ForeignKey(Table, related_name='left_table_name', on_delete=models.CASCADE)
    right_table_name = models.ForeignKey(Table, related_name='right_table_name', on_delete=models.CASCADE)
    join_type = models.CharField(max_length=16, choices=[
        (jt.name, jt.value) for jt in JoinTypes
    ], default=JoinTypes.INNER_JOIN)
    join_condition = models.TextField(default='{{ l }}.column_name = {{ r }}.column_name')

    def __str__(self):
        return json.dumps({attr_name: value for attr_name, value in vars(self).items() if attr_name != '_state'},
                          default=str)

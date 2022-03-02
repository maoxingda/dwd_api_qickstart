import json

from django.db import models


class Table(models.Model):
    TABLE_TYPES = [
        ('dwd', '事实表'),
        ('dim', '维度表'),
    ]
    name = models.CharField(max_length=128, unique=True)
    table_type = models.CharField(max_length=32, choices=TABLE_TYPES, default=TABLE_TYPES[0])

    def columns(self):
        return [column.name for column in self.column_set.all()]

    def __str__(self):
        return self.name


class Column(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Relationship(models.Model):
    JOIN_TYPES = [
        ('IJ', '(INNER) JOIN'),
        ('LJ', 'LEFT (OUTER) JOIN'),
        ('RJ', 'RIGHT (OUTER) JOIN'),
        ('FJ', 'FULL (OUTER) JOIN'),
    ]
    left_table_name = models.ForeignKey(Table, related_name='left_table_name', on_delete=models.CASCADE)
    right_table_name = models.ForeignKey(Table, related_name='right_table_name', on_delete=models.CASCADE)
    join_type = models.CharField(max_length=16, choices=JOIN_TYPES, default=JOIN_TYPES[0])
    join_condition = models.TextField()

    def __str__(self):
        return json.dumps({attr_name: value for attr_name, value in vars(self).items() if attr_name != '_state'}, default=str)

from django.contrib import admin

from graphql_api.models import Relationship, Table, Column


class ColumnInline(admin.StackedInline):
    model = Column


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('name', 'alias', 'table_type', 'columns')
    inlines = [
        ColumnInline,
    ]


@admin.register(Relationship)
class RelationshipsAdmin(admin.ModelAdmin):
    list_display = ('left_table_name', 'right_table_name', 'join_type', 'join_condition')

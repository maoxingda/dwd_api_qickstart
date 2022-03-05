from django.contrib import admin

from graphql_api.forms import RelationshipAdminForm
from graphql_api.models import Relationship, Table, Column

admin.site.site_title = 'dwd API admin'
admin.site.site_header = 'dwd'


class ColumnInline(admin.TabularInline):
    model = Column
    extra = 0


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    search_fields = ('name', 'alias')
    list_filter = ('table_type',)
    list_display = ('name', 'alias', 'table_type')
    inlines = [
        ColumnInline,
    ]


@admin.register(Relationship)
class RelationshipsAdmin(admin.ModelAdmin):
    form = RelationshipAdminForm

    list_filter = ('join_type', 'left_table_name__name', 'right_table_name__name')
    search_fields = ('left_table_name__name', 'right_table_name__name')
    list_display = ('left_table_name', 'join_type', 'right_table_name', 'join_condition')

    autocomplete_fields = ('left_table_name', 'right_table_name')

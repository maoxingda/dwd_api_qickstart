from django.contrib import admin
from admin_auto_filters.filters import AutocompleteFilter

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
    # list_editable = ('alias',)
    inlines = [
        ColumnInline,
    ]

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(
            request, queryset, search_term,
        )

        return queryset, may_have_duplicates

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


class RelationshipsFilter(AutocompleteFilter):
    title = 'left table name'
    field_name = 'left_table_name'


@admin.register(Relationship)
class RelationshipsAdmin(admin.ModelAdmin):
    form = RelationshipAdminForm

    # list_filter = ('join_type', 'left_table_name__name', 'right_table_name__name')
    list_filter = (RelationshipsFilter,)
    search_fields = ('left_table_name__name', 'right_table_name__name')
    list_display = ('left_table_name', 'join_type', 'right_table_name', 'join_condition')

    autocomplete_fields = ('left_table_name', 'right_table_name')

    radio_fields = {"join_type": admin.HORIZONTAL}

    show_full_result_count = False

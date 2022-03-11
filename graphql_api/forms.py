import logging
import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.html import format_html

from graphql_api.models import Relationship, Table
from graphql_api.tools.autogen_schema import dfs

logger = logging.getLogger(__name__)


class RelationshipAdminForm(ModelForm):
    def clean(self):
        super(RelationshipAdminForm, self).clean()

        ltbl = self.cleaned_data['left_table_name']
        rtbl = self.cleaned_data['right_table_name']

        if not self.instance.pk:
            if ltbl.pk == rtbl.pk:
                raise ValidationError(f'{self.cleaned_data["left_table_name"]} can not join with it self.')

            ltr = Relationship.objects.filter(left_table_name__pk=ltbl.pk).filter(right_table_name__pk=rtbl.pk)
            if ltr.count() > 0:
                raise ValidationError(format_html(
                    f'<a href={settings.SERVER_ADDR}/admin/graphql_api/relationship/{ltr[0].pk}/change/>'
                    f'({ltbl.name} ---> {rtbl.name}), already exist.</a>'))

            rtr = Relationship.objects.filter(right_table_name__pk=ltbl.pk).filter(left_table_name__pk=rtbl.pk)
            if rtr.count() > 0:
                raise ValidationError(format_html(
                    f'<a href={settings.SERVER_ADDR}/admin/graphql_api/relationship/{rtr[0].pk}/change/>'
                    f'({rtbl.name} ---> {ltbl.name}), already exist.</a>'))

        # is column name exist?
        columns = re.findall(r'\{\{ \w \}\}\.\w+', self.cleaned_data['join_condition'])
        for column in columns:
            if column.startswith('{{ l }}'):
                if ltbl.column_set.filter(name=column[8:]).count() == 0:
                    raise ValidationError(f'unknown column: {column[8:]}')
            if column.startswith('{{ r }}'):
                if rtbl.column_set.filter(name=column[8:]).count() == 0:
                    raise ValidationError(f'unknown column: {column[8:]}')

        # is dag circle exist?
        tables_children = {}
        for table in Table.objects.all():
            tables_children[table.name] = []
            for relationship in Relationship.objects.all():
                if relationship.left_table_name_id == table.pk:
                    tables_children[table.name].append(relationship.right_table_name.name)

        if ltbl.name in tables_children.keys():
            tables_children[ltbl.name].append(rtbl.name)
        else:
            tables_children[ltbl.name] = [rtbl.name]

        dfs(tables_children, {}, True)

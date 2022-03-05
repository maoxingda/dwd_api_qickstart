import logging
import re

from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.html import format_html

from graphql_api.models import Relationship

logger = logging.getLogger(__name__)


class RelationshipAdminForm(ModelForm):
    def clean(self):
        super(RelationshipAdminForm, self).clean()
        ltbl = self.cleaned_data['left_table_name']
        rtbl = self.cleaned_data['right_table_name']

        if 1 or len(self.changed_data) == 0:
            # TODO: 新增需要校验、改变不需要。如何区分
            if ltbl.id == rtbl.id:
                raise ValidationError(f'{self.cleaned_data["left_table_name"]} can not join with it self.')

            ltr = Relationship.objects.filter(left_table_name__id=ltbl.id).filter(right_table_name__id=rtbl.id)
            if ltr.count() > 0:
                raise ValidationError(format_html(
                    f'<a href=http://127.0.0.1:8000/admin/graphql_api/relationship/{ltr[0].id}/change/>'
                    f'({ltbl.name} <---> {rtbl.name}), already exist.</a>'))

            rtr = Relationship.objects.filter(right_table_name__id=ltbl.id).filter(left_table_name__id=rtbl.id)
            if rtr.count() > 0:
                raise ValidationError(format_html(
                    f'<a href=http://127.0.0.1:8000/admin/graphql_api/relationship/{rtr[0].id}/change/>'
                    f'({rtbl.name} <---> {ltbl.name}), already exist.</a>'))

        # is column name exist?
        columns = re.findall(r'\{\{ \w \}\}\.\w+', self.cleaned_data['join_condition'])
        for column in columns:
            if column.startswith('{{ l }}'):
                if ltbl.column_set.filter(name=column[8:]).count() == 0:
                    raise ValidationError(f'unknown column: {column[8:]}')
            if column.startswith('{{ r }}'):
                if rtbl.column_set.filter(name=column[8:]).count() == 0:
                    raise ValidationError(f'unknown column: {column[8:]}')

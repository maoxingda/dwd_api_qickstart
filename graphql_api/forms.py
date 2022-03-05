import logging
import re

from django.core.exceptions import ValidationError
from django.forms import ModelForm

from graphql_api.models import Relationship

logger = logging.getLogger(__name__)


class RelationshipAdminForm(ModelForm):
    def clean(self):
        super(RelationshipAdminForm, self).clean()
        ltbl = self.cleaned_data['left_table_name']
        rtbl = self.cleaned_data['right_table_name']

        if len(self.changed_data) == 0:
            # TODO: 新增需要校验、改变不需要。如何区分
            if ltbl.id == rtbl.id:
                raise ValidationError(f'{self.cleaned_data["left_table_name"]} can not join with it self.')

            if Relationship.objects.filter(left_table_name__id=ltbl.id).filter(right_table_name__id=rtbl.id).count() > 0:
                raise ValidationError(f'({ltbl.name} <---> {rtbl.name}), already exist.')

            if Relationship.objects.filter(right_table_name__id=ltbl.id).filter(left_table_name__id=rtbl.id).count() > 0:
                raise ValidationError(f'({rtbl.name} <---> {ltbl.name}), already exist.')

        # is column name exist?
        columns = re.findall(r'\{\{ \w \}\}\.\w+', self.cleaned_data['join_condition'])
        for column in columns:
            if column.startswith('{{ l }}'):
                if ltbl.column_set.filter(name=column[8:]).count() == 0:
                    raise ValidationError(f'unknown column: {column[8:]}')
            if column.startswith('{{ r }}'):
                if rtbl.column_set.filter(name=column[8:]).count() == 0:
                    raise ValidationError(f'unknown column: {column[8:]}')

import logging

from django.core.exceptions import ValidationError
from django.forms import ModelForm

from graphql_api.models import Relationship

logger = logging.getLogger(__name__)


class RelationshipAdminForm(ModelForm):
    def clean(self):
        ltbl = self.cleaned_data['left_table_name']
        rtbl = self.cleaned_data['right_table_name']

        if ltbl.id == rtbl.id:
            raise ValidationError(f'{self.cleaned_data["left_table_name"]} can not join with it self.')

        if Relationship.objects.filter(left_table_name__id=ltbl.id).filter(right_table_name__id=rtbl.id).count() > 0:
            raise ValidationError(f'({ltbl.name} <---> {rtbl.name}), already exist.')

        if Relationship.objects.filter(right_table_name__id=ltbl.id).filter(left_table_name__id=rtbl.id).count() > 0:
            raise ValidationError(f'({rtbl.name} <---> {ltbl.name}), already exist.')

from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

from .tools.autogen_schema import build_schema
from .views import update_schema, update_schema_v2

urlpatterns = [
    path('', csrf_exempt(GraphQLView.as_view(schema=build_schema(), graphiql=True))),
    path('updateSchema/', update_schema),
    path('v2/updateSchema/', update_schema_v2),
]

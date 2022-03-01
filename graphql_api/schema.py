import graphene


class Query(graphene.ObjectType):
    """Interfaces"""
    hello = graphene.Field(
        graphene.String,
        greeting=graphene.String(default_value='World!'),
        resolver=lambda parent, context, greeting: 'Hello ' + greeting + '!',
        description='greeting'
    )


schema = graphene.Schema(query=Query)  # type: ignore

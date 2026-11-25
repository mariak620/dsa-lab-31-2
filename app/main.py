from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from app.schema import schema
from app.schema.dataloaders import create_dataloaders


async def get_context() -> dict:
    return create_dataloaders()


graphql_router = GraphQLRouter(
    schema,
    graphql_ide="graphiql",
    context_getter=get_context,
)

app = FastAPI(title="Food Delivery GraphQL API")
app.include_router(graphql_router, prefix="/graphql")
from __future__ import annotations

from typing import Optional

import strawberry

from app.schema.types import CreateOrderInput, OrderType, order_model_to_type, raise_domain_graphql_error
from app.services.orders import accept, cancel, create_order, mark_delivered, mark_ready

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_order(self, input: CreateOrderInput) -> Optional[OrderType]:
        try:
            created = await create_order(
                restaurant_id=int(input.restaurant_id),
                customer_name=input.customer_name,
                delivery_address=input.delivery_address,
                items=[{"dish_id": int(item.dish_id), "quantity": item.quantity} for item in input.items]
            )
            return order_model_to_type(created)
        except Exception as exc:
            raise_domain_graphql_error(exc)
            return None

    @strawberry.mutation
    async def accept_order(self, id: strawberry.ID) -> Optional[OrderType]:
        try:
            updated = await accept(int(id))
            return order_model_to_type(updated)
        except Exception as exc:
            raise_domain_graphql_error(exc)
            return None

    @strawberry.mutation
    async def mark_order_ready(self, id: strawberry.ID) -> Optional[OrderType]:
        try:
            updated = await mark_ready(int(id))
            return order_model_to_type(updated)
        except Exception as exc:
            raise_domain_graphql_error(exc)
            return None

    @strawberry.mutation
    async def mark_order_delivered(self, id: strawberry.ID) -> Optional[OrderType]:
        try:
            updated = await mark_delivered(int(id))
            return order_model_to_type(updated)
        except Exception as exc:
            raise_domain_graphql_error(exc)
            return None

    @strawberry.mutation
    async def cancel_order(self, id: strawberry.ID, reason: str) -> Optional[OrderType]:
        try:
            updated = await cancel(int(id), reason)
            return order_model_to_type(updated)
        except Exception as exc:
            raise_domain_graphql_error(exc)
            return None
from __future__ import annotations

from typing import Optional

import strawberry

from app.db.queries import get_order, list_orders, list_restaurants
from app.schema.types import (
    OrderStatusEnum,
    OrderType,
    RestaurantType,
    order_model_to_type,
)


@strawberry.type
class Query:
    @strawberry.field
    async def order(self, id: strawberry.ID) -> Optional[OrderType]:
        found = await get_order(int(id))
        return order_model_to_type(found) if found is not None else None

    @strawberry.field
    async def orders(self, status: Optional[OrderStatusEnum] = None) -> list[OrderType]:
        rows = await list_orders(status)
        return [order_model_to_type(o) for o in rows]

    @strawberry.field
    async def restaurants(self) -> list[RestaurantType]:
        rows = await list_restaurants()
        return [
            RestaurantType(
                id=strawberry.ID(str(r.id)),
                name=r.name,
                address=r.address,
            )
            for r in rows
        ]
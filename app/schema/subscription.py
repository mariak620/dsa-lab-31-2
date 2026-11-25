from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import strawberry
from graphql import GraphQLError

from app import events
from app.db import queries as db
from app.db.models import OrderStatus
from app.schema.types import OrderType, order_model_to_type

FINAL_STATUSES = {OrderStatus.DELIVERED, OrderStatus.CANCELLED}

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def order_status_changed(
        self,
        order_id: strawberry.ID,
    ) -> AsyncGenerator[OrderType, None]:
        oid = int(order_id)
        queue = events.subscribe(oid)
        try:
            order = await db.get_order(oid)
            if order is None:
                raise GraphQLError(
                    f"Заказ {oid} не найден",
                    extensions={"code": "NOT_FOUND"},
                )

            yield order_model_to_type(order)
            if order.status in FINAL_STATUSES:
                return

            while True:
                event = await queue.get()
                latest = await db.get_order(oid)
                if latest is None:
                    return

                result = order_model_to_type(latest)
                result.status = OrderStatus(event["status"])
                yield result

                if result.status in FINAL_STATUSES:
                    return
        except asyncio.CancelledError:
            raise
        finally:
            events.unsubscribe(oid, queue)
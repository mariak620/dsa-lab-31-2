from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

import strawberry
from strawberry.exceptions import GraphQLError

from app.db.models import Order as OrderModel
from app.db.models import OrderStatus
from app.db.queries import list_dishes
from app.services.errors import NotFound, OrderValidationError, TransitionNotAllowed

OrderStatusEnum = strawberry.enum(OrderStatus)


def raise_domain_graphql_error(exc: Exception) -> None:
    if isinstance(exc, NotFound):
        raise GraphQLError(message=str(exc), extensions={"code": "NOT_FOUND"}) from exc
    if isinstance(exc, TransitionNotAllowed):
        raise GraphQLError(
            message=str(exc),
            extensions={"code": "TRANSITION_NOT_ALLOWED"},
        ) from exc
    if isinstance(exc, OrderValidationError):
        raise GraphQLError(
            message=str(exc),
            extensions={"code": "VALIDATION_ERROR"},
        ) from exc
    raise GraphQLError(message="Internal error", extensions={"code": "INTERNAL_ERROR"}) from exc


@strawberry.type(name="Dish")
class DishType:
    id: strawberry.ID
    name: str
    price: Decimal
    _restaurant_id: strawberry.Private[int]

    @strawberry.field
    async def restaurant(self, info: strawberry.Info) -> "RestaurantType":
        rest = await info.context["restaurant_loader"].load(self._restaurant_id)
        if rest is None:
            raise GraphQLError(message="Ресторан не найден", extensions={"code": "NOT_FOUND"})
        return RestaurantType(
            id=strawberry.ID(str(rest.id)),
            name=rest.name,
            address=rest.address,
        )


@strawberry.type(name="Restaurant")
class RestaurantType:
    id: strawberry.ID
    name: str
    address: str

    @strawberry.field
    async def dishes(self) -> list[DishType]:
        rows = await list_dishes(int(self.id))
        return [
            DishType(
                id=strawberry.ID(str(d.id)),
                name=d.name,
                price=d.price,
                _restaurant_id=d.restaurant_id,
            )
            for d in rows
        ]


@strawberry.type(name="OrderItem")
class OrderItemType:
    quantity: int
    price: Decimal
    _dish_id: strawberry.Private[int]

    @strawberry.field
    async def amount(self) -> Decimal:
        return self.price * Decimal(self.quantity)

    @strawberry.field
    async def dish(self, info: strawberry.Info) -> DishType:
        dish_row = await info.context["dish_loader"].load(self._dish_id)
        if dish_row is None:
            raise GraphQLError(message="Блюдо не найдено", extensions={"code": "NOT_FOUND"})
        return DishType(
            id=strawberry.ID(str(dish_row.id)),
            name=dish_row.name,
            price=dish_row.price,
            _restaurant_id=dish_row.restaurant_id,
        )


@strawberry.type(name="Order")
class OrderType:
    id: strawberry.ID
    status: OrderStatusEnum
    total: Decimal
    created_at: datetime
    customer_name: str
    delivery_address: str
    cancel_reason: Optional[str]
    _restaurant_id: strawberry.Private[int]
    _order_id: strawberry.Private[int]

    @strawberry.field
    async def restaurant(self, info: strawberry.Info) -> RestaurantType:
        rest = await info.context["restaurant_loader"].load(self._restaurant_id)
        if rest is None:
            raise GraphQLError(message="Ресторан не найден", extensions={"code": "NOT_FOUND"})
        return RestaurantType(
            id=strawberry.ID(str(rest.id)),
            name=rest.name,
            address=rest.address,
        )

    @strawberry.field
    async def items(self, info: strawberry.Info) -> list[OrderItemType]:
        rows = await info.context["items_loader"].load(self._order_id)
        return [
            OrderItemType(
                quantity=item.quantity,
                price=item.price,
                _dish_id=item.dish_id,
            )
            for item in rows
        ]


def order_model_to_type(order_row: OrderModel) -> OrderType:
    return OrderType(
        id=strawberry.ID(str(order_row.id)),
        status=order_row.status,
        total=order_row.total,
        created_at=order_row.created_at,
        customer_name=order_row.customer_name,
        delivery_address=order_row.delivery_address,
        cancel_reason=order_row.cancel_reason,
        _restaurant_id=order_row.restaurant_id,
        _order_id=order_row.id,
    )

@strawberry.input
class CreateOrderItemInput:
    dish_id: strawberry.ID
    quantity: int

@strawberry.input
class CreateOrderInput:
    restaurant_id: strawberry.ID
    customer_name: str
    delivery_address: str
    items: list[CreateOrderItemInput]
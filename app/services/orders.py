from decimal import Decimal
from typing import Any

from app import events
from app.db import queries as db
from app.db.engine import SessionLocal
from app.db.models import Dish, Order, OrderItem, OrderStatus
from app.services.errors import NotFound, OrderValidationError, TransitionNotAllowed

FINAL_STATUSES = {OrderStatus.DELIVERED, OrderStatus.CANCELLED}

TRANSITIONS: dict[str, tuple[set[OrderStatus], OrderStatus]] = {
    "accept": ({OrderStatus.CREATED}, OrderStatus.ACCEPTED),
    "mark_ready": ({OrderStatus.ACCEPTED}, OrderStatus.READY),
    "mark_delivered": ({OrderStatus.READY}, OrderStatus.DELIVERED),
    "cancel": ({OrderStatus.CREATED, OrderStatus.ACCEPTED}, OrderStatus.CANCELLED),
}


async def _apply_transition(
    order_id: int,
    action: str,
    reason: str | None = None,
) -> Order:
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        if order is None:
            raise NotFound(f"Заказ {order_id} не найден")

        allowed_sources, target_status = TRANSITIONS[action]
        if order.status not in allowed_sources:
            raise TransitionNotAllowed(
                f"Действие {action} недопустимо в состоянии {order.status.value}"
            )

        if action == "cancel":
            if reason is None or not (3 <= len(reason) <= 200):
                raise OrderValidationError("Причина отмены должна быть от 3 до 200 символов")
            order.cancel_reason = reason

        order.status = target_status
        await session.commit()
        await session.refresh(order)

    await events.publish({"order_id": order.id, "status": order.status.value})
    return order


async def accept(order_id: int) -> Order:
    return await _apply_transition(order_id, "accept")


async def mark_ready(order_id: int) -> Order:
    return await _apply_transition(order_id, "mark_ready")


async def mark_delivered(order_id: int) -> Order:
    return await _apply_transition(order_id, "mark_delivered")


async def cancel(order_id: int, reason: str) -> Order:
    return await _apply_transition(order_id, "cancel", reason=reason)


async def create_order(
    restaurant_id: int,
    customer_name: str,
    delivery_address: str,
    items: list[dict[str, Any]],
) -> Order:
    restaurant = await db.get_restaurant(restaurant_id)
    if restaurant is None:
        raise NotFound(f"Ресторан {restaurant_id} не найден")

    if not (1 <= len(items) <= 10):
        raise OrderValidationError("В заказе должно быть от 1 до 10 позиций")

    dish_ids = [int(item["dish_id"]) for item in items]
    if len(set(dish_ids)) != len(dish_ids):
        raise OrderValidationError("Одно блюдо может входить в заказ только одной позицией")

    dishes_map: dict[int, Dish] = await db.get_dishes(dish_ids)

    total = Decimal("0.00")
    order_items: list[OrderItem] = []

    for item in items:
        dish_id = int(item["dish_id"])
        dish = dishes_map.get(dish_id)
        if dish is None:
            raise NotFound(f"Блюдо {dish_id} не найдено")

        if dish.restaurant_id != restaurant_id:
            raise OrderValidationError("Все блюда заказа должны принадлежать выбранному ресторану")

        qty = int(item["quantity"])
        if not (1 <= qty <= 20):
            raise OrderValidationError("Количество порций должно быть от 1 до 20")

        total += dish.price * Decimal(qty)
        order_items.append(
            OrderItem(
                dish_id=dish.id,
                quantity=qty,
                price=dish.price,
            )
        )

    async with SessionLocal() as session:
        order = Order(
            restaurant_id=restaurant_id,
            customer_name=customer_name,
            delivery_address=delivery_address,
            status=OrderStatus.CREATED,
            total=total,
            items=order_items,
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)

    await events.publish({"order_id": order.id, "status": order.status.value})
    return order
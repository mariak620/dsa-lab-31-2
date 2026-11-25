from typing import Optional, Sequence
from sqlalchemy import select

from app.db.engine import SessionLocal
from app.db.models import Dish, Order, OrderItem, OrderStatus, Restaurant


async def get_restaurant(restaurant_id: int) -> Optional[Restaurant]:
    async with SessionLocal() as session:
        result = await session.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
        return result.scalar_one_or_none()


async def list_restaurants() -> Sequence[Restaurant]:
    async with SessionLocal() as session:
        result = await session.execute(select(Restaurant).order_by(Restaurant.id))
        return result.scalars().all()


async def get_dish(dish_id: int) -> Optional[Dish]:
    async with SessionLocal() as session:
        result = await session.execute(select(Dish).where(Dish.id == dish_id))
        return result.scalar_one_or_none()


async def list_dishes(restaurant_id: int) -> Sequence[Dish]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Dish).where(Dish.restaurant_id == restaurant_id).order_by(Dish.id)
        )
        return result.scalars().all()


async def get_order(order_id: int) -> Optional[Order]:
    async with SessionLocal() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()


async def get_items(order_id: int) -> Sequence[OrderItem]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(OrderItem).where(OrderItem.order_id == order_id).order_by(OrderItem.id)
        )
        return result.scalars().all()


async def list_orders(status: Optional[OrderStatus] = None) -> Sequence[Order]:
    async with SessionLocal() as session:
        stmt = select(Order)
        if status is not None:
            stmt = stmt.where(Order.status == status)
        stmt = stmt.order_by(Order.created_at.desc(), Order.id.desc())
        result = await session.execute(stmt)
        return result.scalars().all()


async def get_restaurants(ids: list[int]) -> dict[int, Restaurant]:
    if not ids:
        return {}
    async with SessionLocal() as session:
        result = await session.execute(select(Restaurant).where(Restaurant.id.in_(ids)))
        return {x.id: x for x in result.scalars().all()}


async def get_dishes(ids: list[int]) -> dict[int, Dish]:
    if not ids:
        return {}
    async with SessionLocal() as session:
        result = await session.execute(select(Dish).where(Dish.id.in_(ids)))
        return {x.id: x for x in result.scalars().all()}


async def get_items_by_orders(order_ids: list[int]) -> dict[int, list[OrderItem]]:
    mapping: dict[int, list[OrderItem]] = {oid: [] for oid in order_ids}
    if not order_ids:
        return mapping
    async with SessionLocal() as session:
        result = await session.execute(
            select(OrderItem).where(OrderItem.order_id.in_(order_ids)).order_by(OrderItem.id)
        )
        for item in result.scalars().all():
            mapping[item.order_id].append(item)
        return mapping
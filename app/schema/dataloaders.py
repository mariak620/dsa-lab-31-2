from strawberry.dataloader import DataLoader

from app.db import queries as db
from app.db.models import Dish, OrderItem, Restaurant


async def load_restaurants(keys: list[int]) -> list[Restaurant | None]:
    mapping = await db.get_restaurants(keys)
    return [mapping.get(k) for k in keys]


async def load_dishes(keys: list[int]) -> list[Dish | None]:
    mapping = await db.get_dishes(keys)
    return [mapping.get(k) for k in keys]


async def load_order_items(keys: list[int]) -> list[list[OrderItem]]:
    mapping = await db.get_items_by_orders(keys)
    return [mapping.get(k, []) for k in keys]


def create_dataloaders() -> dict[str, DataLoader]:
    return {
        "restaurant_loader": DataLoader(load_fn=load_restaurants),
        "dish_loader": DataLoader(load_fn=load_dishes),
        "items_loader": DataLoader(load_fn=load_order_items),
    }
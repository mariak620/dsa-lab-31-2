import asyncio, random
from decimal import Decimal
from datetime import datetime, timedelta
from app.db.engine import SessionLocal, engine
from app.db.models import Base, Restaurant, Dish, Order, OrderItem, OrderStatus


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as s:
        rests = []
        for i in range(5):
            r = Restaurant(name=f"Ресторан {i+1}", address=f"ул. Тестовая, {i+1}")
            s.add(r); rests.append(r)
        await s.flush()
        dishes_by_rest = {}
        for r in rests:
            lst = []
            for j in range(10):
                d = Dish(restaurant_id=r.id, name=f"Блюдо {r.id}-{j+1}",
                         price=Decimal(random.randint(100, 1000)))
                s.add(d); lst.append(d)
            dishes_by_rest[r.id] = lst
        await s.flush()

        statuses = list(OrderStatus)
        for k in range(100):
            r = random.choice(rests)
            st = statuses[k % len(statuses)]
            reason = "Причина отмены" if st == OrderStatus.CANCELLED else None
            items = []
            total = Decimal("0.00")
            picked = random.sample(dishes_by_rest[r.id], k=random.randint(1, 10))
            for d in picked:
                qty = random.randint(1, 20)
                total += d.price * qty
                items.append(OrderItem(dish_id=d.id, quantity=qty, price=d.price))
            o = Order(restaurant_id=r.id, customer_name=f"Клиент {k+1}",
                      delivery_address=f"Адрес {k+1}", status=st,
                      cancel_reason=reason, total=total, items=items,
                      created_at=datetime.utcnow() - timedelta(minutes=k))
            s.add(o)
        await s.commit()


asyncio.run(main())
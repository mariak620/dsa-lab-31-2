import asyncio
from collections import defaultdict
from typing import Any

_subscribers: dict[int, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)


def subscribe(order_id: int) -> asyncio.Queue[dict[str, Any]]:
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    _subscribers[int(order_id)].add(queue)
    return queue


def unsubscribe(order_id: int, queue: asyncio.Queue[dict[str, Any]]) -> None:
    oid = int(order_id)
    queues = _subscribers.get(oid)
    if not queues:
        return
    queues.discard(queue)
    if not queues:
        _subscribers.pop(oid, None)


async def publish(event: dict[str, Any]) -> None:
    raw_order_id = event.get("order_id") if "order_id" in event else event.get("orderId")
    if raw_order_id is None:
        return
    oid = int(raw_order_id)
    for queue in list(_subscribers.get(oid, ())):
        await queue.put(event)
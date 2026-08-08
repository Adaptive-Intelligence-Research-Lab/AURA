"""
Event Bus — AURA-007, AURA-SPEC-003

In-process, asyncio-based event distribution.

v0.1 dispatch model:
- Synchronous sequential dispatch (await each subscriber in registration order)
- No queues, no background tasks, no priority ordering
- Subscriber exception isolation
- Lifecycle: start() / stop() flags
"""
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable

from ...models.events import Event, EventType

logger = logging.getLogger(__name__)


class EventBus:
    """
    In-process event bus using asyncio.

    Supports:
    - Asynchronous subscribers
    - Event filtering by type
    - Exception isolation
    - Deterministic sequential dispatch

    v0.1 ordering guarantees:
    - Subscribers for a given event type execute sequentially
      in registration order (await each callback before the next)
    - Multiple events published sequentially arrive in publish order
    - Global ordering across unrelated concurrent publish calls
      is NOT guaranteed
    """

    def __init__(self) -> None:
        """Initialize the Event Bus."""
        self._subscribers: dict[EventType, list[Callable]] = defaultdict(list)
        self._running = False

    async def start(self) -> None:
        """
        Start the event bus.

        Marks the bus as running. Publish calls are only
        allowed while the bus is running.
        """
        self._running = True
        logger.info("Event bus started")

    async def stop(self) -> None:
        """
        Stop the event bus.

        Marks the bus as stopped. Publish calls after stop
        will raise RuntimeError.
        """
        self._running = False
        logger.info("Event bus stopped")

    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        Subscribe to an event type.

        Subscribers receive events asynchronously.
        Subscriber failures are isolated — one failing
        subscriber does not prevent others from receiving events.

        Args:
            event_type: The event type to listen for
            callback: Async callable receiving the event
        """
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type}: {callback}")

    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        Remove an event subscription.

        Args:
            event_type: The event type to unsubscribe from
            callback: The callback to remove
        """
        if callback in self._subscribers.get(event_type, []):
            self._subscribers[event_type].remove(callback)
            logger.debug(f"Unsubscribed from {event_type}: {callback}")

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.

        Dispatches sequentially: each subscriber is awaited in
        registration order before the next is called.

        Subscriber failures are isolated — one failing subscriber
        does not prevent others from receiving the event.

        Raises:
            RuntimeError: If the bus is not running.

        Args:
            event: The event to publish
        """
        if not self._running:
            raise RuntimeError("EventBus is not running")

        callbacks = self._subscribers.get(event.event_type, [])

        for callback in callbacks:
            try:
                await callback(event)
            except Exception:
                logger.exception(
                    f"Subscriber error for {event.event_type}",
                )
                # Isolate — continue processing other subscribers

    async def publish_many(self, events: list[Event]) -> None:
        """
        Publish multiple events sequentially.

        Args:
            events: List of events to publish
        """
        for event in events:
            await self.publish(event)

    def get_subscriber_count(self, event_type: EventType) -> int:
        """
        Get the number of subscribers for an event type.

        Args:
            event_type: The event type to count

        Returns:
            Number of active subscribers
        """
        return len(self._subscribers.get(event_type, []))

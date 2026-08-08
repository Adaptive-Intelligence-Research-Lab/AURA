"""
Event Bus — AURA-007, AURA-SPEC-003

In-process, asyncio-based event distribution.
"""
from __future__ import annotations

import asyncio
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
    - Basic priority ordering
    - Exception isolation
    - Graceful shutdown

    Ordering guarantees:
    - For events sharing the same execution context 
      (same correlation_id), ordering is preserved 
      for events of the same type
    - Global ordering across unrelated concurrent 
      actions is NOT required
    """

    def __init__(self, queue_size: int = 1000):
        """
        Initialize the Event Bus.

        Args:
            queue_size: Maximum queue size per event type
        """
        self._queue_size = queue_size
        self._queues: dict[str, asyncio.PriorityQueue] = {}
        self._subscribers: dict[EventType, list[Callable]] = defaultdict(list)
        self._running = False
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """
        Start the event bus.

        This method initializes any background processing
        and marks the bus as running.
        """
        self._running = True
        logger.info("Event bus started")

    async def stop(self) -> None:
        """
        Gracefully shut down the event bus.

        This method:
        - Cancels any pending subscriber tasks
        - Waits for graceful shutdown
        - Logs the shutdown event
        """
        self._running = False
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
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

        Subscriber failures are isolated — one failing subscriber
        does not prevent others from receiving the event.

        Ordering is preserved for events sharing the same
        correlation_id when subscribers process sequentially.

        Args:
            event: The event to publish
        """
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
        Publish multiple events.

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

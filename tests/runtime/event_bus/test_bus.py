"""Tests for the Event Bus."""
from uuid import uuid4

import pytest

from aura.models.events import Event, EventType
from aura.runtime.event_bus.bus import EventBus


@pytest.fixture
async def event_bus():
    """Create and start an event bus."""
    bus = EventBus()
    await bus.start()
    yield bus
    await bus.stop()


class TestEventBus:
    """Tests for EventBus core functionality."""

    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self, event_bus):
        """Events should reach subscribers."""
        received = []

        async def handler(event: Event):
            received.append(event)

        event_bus.subscribe(EventType.ACTION_CREATED, handler)

        event = Event(
            event_type=EventType.ACTION_CREATED,
            source="test",
            payload={"action_id": str(uuid4())}
        )
        await event_bus.publish(event)

        assert len(received) == 1
        assert received[0] == event

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, event_bus):
        """All subscribers should receive events."""
        received_a = []
        received_b = []

        async def handler_a(event: Event):
            received_a.append(event)

        async def handler_b(event: Event):
            received_b.append(event)

        event_bus.subscribe(EventType.ACTION_COMPLETED, handler_a)
        event_bus.subscribe(EventType.ACTION_COMPLETED, handler_b)

        event = Event(
            event_type=EventType.ACTION_COMPLETED,
            source="test",
            payload={"action_id": str(uuid4())}
        )
        await event_bus.publish(event)

        assert len(received_a) == 1
        assert len(received_b) == 1

    @pytest.mark.asyncio
    async def test_no_subscribers(self, event_bus):
        """Publishing to unmapped event should not raise."""
        event = Event(
            event_type=EventType.RUNTIME_STARTED,
            source="test",
            payload={}
        )
        await event_bus.publish(event)

    @pytest.mark.asyncio
    async def test_subscriber_error_isolation(self, event_bus):
        """One failing subscriber should not break others."""
        received = []

        async def failing_handler(event: Event):
            raise RuntimeError("Test error")

        async def good_handler(event: Event):
            received.append(event)

        event_bus.subscribe(EventType.ACTION_CREATED, failing_handler)
        event_bus.subscribe(EventType.ACTION_CREATED, good_handler)

        event = Event(
            event_type=EventType.ACTION_CREATED,
            source="test",
            payload={"action_id": str(uuid4())}
        )
        await event_bus.publish(event)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_event_correlation(self, event_bus):
        """Events should carry correlation IDs."""
        received = []

        async def handler(event: Event):
            received.append(event)

        event_bus.subscribe(EventType.ACTION_STARTED, handler)

        correlation_id = uuid4()
        event = Event(
            event_type=EventType.ACTION_STARTED,
            correlation_id=correlation_id,
            source="test",
            payload={"action_id": str(uuid4())}
        )
        await event_bus.publish(event)

        assert received[0].correlation_id == correlation_id

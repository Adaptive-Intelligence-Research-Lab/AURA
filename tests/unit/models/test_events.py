"""Tests for Event model — AURA-SPEC-003."""
from datetime import UTC, datetime
from uuid import UUID

import pytest

from aura.models.events import Event, EventType


class TestEventType:
    def test_action_lifecycle_events(self):
        assert EventType.ACTION_CREATED == "ActionCreated"
        assert EventType.ACTION_VALIDATED == "ActionValidated"
        assert EventType.ACTION_STARTED == "ActionStarted"
        assert EventType.ACTION_COMPLETED == "ActionCompleted"
        assert EventType.ACTION_FAILED == "ActionFailed"

    def test_capability_events(self):
        assert EventType.CAPABILITY_REGISTERED == "CapabilityRegistered"
        assert EventType.CAPABILITY_UNREGISTERED == "CapabilityUnregistered"

    def test_runtime_events(self):
        assert EventType.RUNTIME_STARTED == "RuntimeStarted"
        assert EventType.RUNTIME_STOPPED == "RuntimeStopped"

    def test_all_nine_types(self):
        assert len(EventType) == 9


class TestEvent:
    def test_event_is_frozen(self):
        event = Event(
            event_type=EventType.ACTION_CREATED,
            source="test",
        )
        with pytest.raises(AttributeError):
            event.source = "other"  # type: ignore[misc]

    def test_event_has_unique_id(self):
        e1 = Event(event_type=EventType.ACTION_CREATED, source="test")
        e2 = Event(event_type=EventType.ACTION_CREATED, source="test")
        assert e1.event_id != e2.event_id

    def test_event_has_timestamp(self):
        before = datetime.now(UTC)
        event = Event(event_type=EventType.ACTION_CREATED, source="test")
        after = datetime.now(UTC)
        assert before <= event.timestamp <= after
        assert event.timestamp.tzinfo is UTC

    def test_event_has_correlation_id(self):
        event = Event(event_type=EventType.ACTION_CREATED, source="test")
        assert isinstance(event.correlation_id, UUID)

    def test_event_schema_version(self):
        event = Event(event_type=EventType.ACTION_CREATED, source="test")
        assert event.schema_version == "1.0.0"

    def test_event_with_payload(self):
        event = Event(
            event_type=EventType.ACTION_CREATED,
            source="test",
            payload={"action_id": "123"},
        )
        assert event.payload == {"action_id": "123"}

    def test_to_dict(self):
        event = Event(
            event_type=EventType.ACTION_COMPLETED,
            source="executor",
            payload={"output": {"message": "hi"}},
        )
        d = event.to_dict()
        assert d["event_type"] == "ActionCompleted"
        assert d["source"] == "executor"
        assert d["schema_version"] == "1.0.0"
        assert "event_id" in d
        assert "timestamp" in d
        assert "correlation_id" in d

    def test_to_dict_payload(self):
        event = Event(
            event_type=EventType.ACTION_CREATED,
            source="test",
            payload={"key": "value"},
        )
        d = event.to_dict()
        assert d["payload"] == {"key": "value"}

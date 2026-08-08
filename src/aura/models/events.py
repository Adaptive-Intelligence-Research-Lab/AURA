"""
Event Model — AURA-SPEC-003

Events represent immutable facts about runtime activity.
Every significant runtime state transition produces an event.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
from datetime import datetime, timezone


class EventType(str, Enum):
    """
    Canonical event types that the runtime publishes.

    These are the minimum events required by AURA v0.1.
    """
    # Action lifecycle events
    ACTION_CREATED = "ActionCreated"
    ACTION_VALIDATED = "ActionValidated"
    ACTION_STARTED = "ActionStarted"
    ACTION_COMPLETED = "ActionCompleted"
    ACTION_FAILED = "ActionFailed"

    # Capability lifecycle events
    CAPABILITY_REGISTERED = "CapabilityRegistered"
    CAPABILITY_UNREGISTERED = "CapabilityUnregistered"

    # Runtime lifecycle events
    RUNTIME_STARTED = "RuntimeStarted"
    RUNTIME_STOPPED = "RuntimeStopped"


@dataclass(frozen=True)
class Event:
    """
    An immutable fact representing something that occurred in the runtime.

    Events SHALL:
    - Have a unique Event ID
    - Declare an Event Type
    - Include a timestamp
    - Be immutable
    - Be serializable
    - Be versioned

    Events NEVER express commands or requests.
    """
    event_type: EventType
    source: str
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    correlation_id: UUID = field(default_factory=uuid4)
    payload: dict[str, Any] = field(default_factory=dict)
    schema_version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": str(self.correlation_id),
            "source": self.source,
            "payload": self.payload,
            "schema_version": self.schema_version,
        }
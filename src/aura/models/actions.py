"""
Action Model — AURA-SPEC-002

An Action represents a concrete request to execute a capability.
Actions are the canonical execution message exchanged throughout
the Adaptive Intelligence Runtime.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4
from datetime import datetime, timezone


@dataclass
class ActionPolicy:
    """
    Execution policy for an action.

    Defines timeout, retry, and scheduling behavior.
    This model is intentionally simple for v0.1.
    Advanced policies will be added in later versions.
    """
    timeout_ms: int = 30000
    retry_count: int = 0


@dataclass
class Action:
    """
    A concrete request to execute a capability.

    Actions SHALL have unique identifiers.
    Actions SHALL be immutable after execution begins
    (enforced by the runtime, not the model itself).
    """
    capability_id: str
    parameters: dict[str, Any] = field(default_factory=dict)
    execution_policy: ActionPolicy = field(default_factory=ActionPolicy)
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Auto-generated fields
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
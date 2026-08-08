"""
Execution Result Model — AURA-SPEC-002

Structured result returned by every capability execution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone


class ExecutionStatus(str, Enum):
    """Execution completion status."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """
    Structured result of a capability execution.

    Execution providers SHALL NOT return arbitrary unstructured values.
    They SHALL return structured results through the runtime.
    """
    action_id: UUID
    status: ExecutionStatus
    execution_id: UUID = field(default_factory=uuid4)
    output: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Whether execution was successful."""
        return self.status == ExecutionStatus.SUCCESS
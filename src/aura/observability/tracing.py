"""Basic correlation tracing for AURA runtime."""
from __future__ import annotations

from uuid import UUID


class TraceContext:
    """Holds correlation identifiers for a single execution lifecycle."""

    def __init__(
        self,
        correlation_id: UUID,
        action_id: UUID | None = None,
        execution_id: UUID | None = None,
    ) -> None:
        self.correlation_id = correlation_id
        self.action_id = action_id
        self.execution_id = execution_id

    def to_dict(self) -> dict[str, str | None]:
        return {
            "correlation_id": str(self.correlation_id),
            "action_id": str(self.action_id) if self.action_id else None,
            "execution_id": str(self.execution_id) if self.execution_id else None,
        }

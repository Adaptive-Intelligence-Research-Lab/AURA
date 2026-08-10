"""
Capability Executor — AURA-IMPL-001 §24

Execution sequence (spec §28):
  1. Validate Action (provider.validate)
  2. ActionValidated event
  3. Governance Check
  4. ActionStarted event (state = RUNNING)
  5. Execute Provider
  6. ActionCompleted / ActionFailed event
  7. Return structured ExecutionResult
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import UTC, datetime

from ..models.actions import Action
from ..models.capabilities import CapabilityProvider
from ..models.events import Event, EventType
from ..models.execution import ExecutionResult, ExecutionStatus
from ..runtime.event_bus.bus import EventBus
from ..runtime.governance.gate import GovernanceGate

logger = logging.getLogger(__name__)


class CapabilityExecutor:
    """
    Executes capabilities with governance, validation, and error handling.

    The Executor is a stateless orchestrator. It uses injected
    dependencies (EventBus, GovernanceGate, CapabilityProvider)
    to perform execution.
    """

    def __init__(self, event_bus: EventBus, governance: GovernanceGate) -> None:
        self._event_bus = event_bus
        self._governance = governance

    async def execute(
        self, action: Action, provider: CapabilityProvider
    ) -> ExecutionResult:
        """
        Execute a capability with full lifecycle management.

        Args:
            action: The action to execute
            provider: The capability provider to invoke

        Returns:
            ExecutionResult with success/error status
        """
        action_id = action.id
        cap_id = action.capability_id
        correlation_id = action.correlation_id
        execution_id = uuid.uuid4()
        start_time = time.time()

        # Step 1: Validate action (provider.validate)
        try:
            validated_params = provider.validate(action.parameters)
        except Exception as e:  # noqa: BLE001
            duration = (time.time() - start_time) * 1000
            await self._publish(
                EventType.ACTION_FAILED, action_id, cap_id, correlation_id,
                {"error": str(e), "error_type": "validation"},
            )
            return ExecutionResult(
                action_id=action_id,
                execution_id=execution_id,
                status=ExecutionStatus.FAILURE,
                capability_id=cap_id,
                output=None,
                error=f"Validation error: {e}",
                started_at=action.created_at,
                completed_at=datetime.now(UTC),
                metadata={"duration_ms": duration},
            )

        # Step 2: Publish ActionValidated
        await self._publish(
            EventType.ACTION_VALIDATED, action_id, cap_id, correlation_id
        )

        # Step 3: Governance check
        decision = self._governance.check(action)
        if not decision.allowed:
            duration = (time.time() - start_time) * 1000
            await self._publish(
                EventType.ACTION_FAILED, action_id, cap_id, correlation_id,
                {"error": f"Governance denied: {decision.reason}", "error_type": "governance"},
            )
            return ExecutionResult(
                action_id=action_id,
                execution_id=execution_id,
                status=ExecutionStatus.FAILURE,
                capability_id=cap_id,
                output=None,
                error=f"Governance denied: {decision.reason}",
                started_at=action.created_at,
                completed_at=datetime.now(UTC),
                metadata={"duration_ms": duration},
            )

        # Step 4: Publish ActionStarted (state = RUNNING)
        await self._publish(
            EventType.ACTION_STARTED, action_id, cap_id, correlation_id
        )

        # Step 5: Execute provider
        try:
            output = await provider.execute(validated_params)
        except Exception as e:  # noqa: BLE001
            duration = (time.time() - start_time) * 1000
            await self._publish(
                EventType.ACTION_FAILED, action_id, cap_id, correlation_id,
                {"error": str(e), "error_type": "execution"},
            )
            return ExecutionResult(
                action_id=action_id,
                execution_id=execution_id,
                status=ExecutionStatus.FAILURE,
                capability_id=cap_id,
                output=None,
                error=f"Execution error: {e}",
                started_at=action.created_at,
                completed_at=datetime.now(UTC),
                metadata={"duration_ms": duration},
            )

        # Step 6: Publish ActionCompleted
        duration = (time.time() - start_time) * 1000
        await self._publish(
            EventType.ACTION_COMPLETED, action_id, cap_id, correlation_id,
            {"output": output},
        )

        return ExecutionResult(
            action_id=action_id,
            execution_id=execution_id,
            status=ExecutionStatus.SUCCESS,
            capability_id=cap_id,
            output=output,
            started_at=action.created_at,
            completed_at=datetime.now(UTC),
            metadata={"duration_ms": duration},
        )

    async def _publish(
        self,
        event_type: EventType,
        action_id: uuid.UUID,
        capability_id: str,
        correlation_id: uuid.UUID,
        extra_payload: dict | None = None,
    ) -> None:
        """Publish an event to the event bus with correlation_id propagation."""
        payload: dict = {
            "action_id": str(action_id),
            "capability_id": capability_id,
        }
        if extra_payload:
            payload.update(extra_payload)

        event = Event(
            event_type=event_type,
            source="executor",
            payload=payload,
            correlation_id=correlation_id,
        )
        await self._event_bus.publish(event)

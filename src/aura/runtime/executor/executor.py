"""
Capability Executor — AURA-010

The Executor orchestrates capability execution by:
  1. Governance check (GovernanceGate)
  2. Input validation (CapabilityProvider.validate)
  3. Provider invocation (CapabilityProvider.execute)
  4. Result packaging

The executor SHALL NOT modify runtime state directly.
It SHALL publish events through the EventBus.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from ...models.actions import Action
from ...models.capabilities import CapabilityProvider
from ...models.events import Event, EventType
from ..event_bus.bus import EventBus
from ..governance.gate import GovernanceGate

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """
    Result of a capability execution.

    The result always pairs an output with execution metadata,
    allowing the caller to make informed decisions.
    """
    action_id: str
    capability_id: str
    success: bool
    output: dict[str, Any]
    error: Optional[str] = None
    duration_ms: Optional[float] = None


class CapabilityExecutor:
    """
    Executes capabilities with governance, validation, and error handling.

    The Executor is a stateless orchestrator. It uses injected
    dependencies (EventBus, GovernanceGate, CapabilityProvider)
    to perform execution.
    """

    def __init__(
        self,
        event_bus: EventBus,
        governance: GovernanceGate,
    ):
        """
        Initialize the executor.

        Args:
            event_bus: The runtime event bus for publishing events
            governance: The governance gate for capability checks
        """
        self._event_bus = event_bus
        self._governance = governance

    async def execute(
        self,
        action: Action,
        provider: CapabilityProvider,
    ) -> ExecutionResult:
        """
        Execute a capability with full lifecycle management.

        Args:
            action: The action to execute
            provider: The capability provider to invoke

        Returns:
            ExecutionResult with success/error status
        """
        import time

        action_id = str(action.id)
        cap_id = action.capability_id
        start_time = time.time()

        # 1. Governance check
        decision = self._governance.check(action)
        if not decision.allowed:
            result = ExecutionResult(
                action_id=action_id,
                capability_id=cap_id,
                success=False,
                output={},
                error=f"Governance denied: {decision.reason or 'unknown'}",
            )
            return result

        # 2. Publish validated event
        await self._publish_event(
            EventType.ACTION_VALIDATED,
            action_id,
            cap_id,
        )

        # 3. Publish started event
        await self._publish_event(
            EventType.ACTION_STARTED,
            action_id,
            cap_id,
        )

        try:
            # 4. Validate input parameters
            try:
                validated_params = provider.validate(action.parameters)
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                result = ExecutionResult(
                    action_id=action_id,
                    capability_id=cap_id,
                    success=False,
                    output={},
                    error=f"Validation error: {e}",
                    duration_ms=duration,
                )
                await self._publish_event(
                    EventType.ACTION_FAILED,
                    action_id,
                    cap_id,
                    {"error": str(e)},
                )
                return result

            # 5. Execute the capability
            try:
                output = await provider.execute(validated_params)
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(
                    f"Execution error for {cap_id} "
                    f"(action {action_id}): {e}"
                )
                result = ExecutionResult(
                    action_id=action_id,
                    capability_id=cap_id,
                    success=False,
                    output={},
                    error=f"Execution error: {e}",
                    duration_ms=duration,
                )
                await self._publish_event(
                    EventType.ACTION_FAILED,
                    action_id,
                    cap_id,
                    {"error": str(e)},
                )
                return result

            # 6. Publish completed event
            duration = (time.time() - start_time) * 1000
            result = ExecutionResult(
                action_id=action_id,
                capability_id=cap_id,
                success=True,
                output=output,
                duration_ms=duration,
            )
            await self._publish_event(
                EventType.ACTION_COMPLETED,
                action_id,
                cap_id,
                {"output": output},
            )
            return result

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"Unexpected error executing {cap_id} "
                f"(action {action_id}): {e}"
            )
            result = ExecutionResult(
                action_id=action_id,
                capability_id=cap_id,
                success=False,
                output={},
                error=f"Unexpected error: {e}",
                duration_ms=duration,
            )
            await self._publish_event(
                EventType.ACTION_FAILED,
                action_id,
                cap_id,
                {"error": str(e)},
            )
            return result

    async def _publish_event(
        self,
        event_type: EventType,
        action_id: str,
        capability_id: str,
        extra_payload: Optional[dict] = None,
    ) -> None:
        """Publish an event to the event bus."""
        payload = {
            "action_id": action_id,
            "capability_id": capability_id,
        }
        if extra_payload:
            payload.update(extra_payload)

        event = Event(
            event_type=event_type,
            source="executor",
            payload=payload,
        )
        await self._event_bus.publish(event)

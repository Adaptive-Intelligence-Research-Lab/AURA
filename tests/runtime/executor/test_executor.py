"""Tests for the CapabilityExecutor."""
import pytest
import asyncio
from uuid import uuid4

from aura.runtime.executor.executor import CapabilityExecutor, ExecutionResult
from aura.runtime.event_bus.bus import EventBus
from aura.runtime.governance.gate import GovernanceGate
from aura.models.actions import Action, ActionPolicy
from aura.models.capabilities import (
    CapabilityProvider,
    CapabilityMetadata,
    RiskLevel,
)
from aura.models.events import Event, EventType


class MockCapabilityProvider(CapabilityProvider):
    """Mock capability provider for testing."""

    @property
    def metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            id="test.mock",
            version="1.0.0",
            name="Mock Capability",
            description="Test capability",
            input_schema={"message": {"type": "string"}},
            output_schema={"result": {"type": "string"}},
            permissions=[],
            risk_level=RiskLevel.MINIMAL,
        )

    def validate(self, parameters: dict) -> dict:
        if "message" not in parameters:
            raise ValueError("Missing 'message' parameter")
        return {"message": parameters["message"]}

    async def execute(self, parameters: dict) -> dict:
        return {"result": f"Echo: {parameters['message']}"}


class FailingCapabilityProvider(CapabilityProvider):
    """Capability provider that fails validation."""

    @property
    def metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            id="test.failing",
            version="1.0.0",
            name="Failing Capability",
            description="Test capability that fails",
            input_schema={},
            output_schema={},
            permissions=[],
            risk_level=RiskLevel.MINIMAL,
        )

    def validate(self, parameters: dict) -> dict:
        raise ValueError("Validation always fails")

    async def execute(self, parameters: dict) -> dict:
        return {}


class TestCapabilityExecutor:
    """Tests for CapabilityExecutor."""

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Executor runs valid action successfully."""
        bus = EventBus()
        await bus.start()
        governance = GovernanceGate()
        executor = CapabilityExecutor(bus, governance)

        provider = MockCapabilityProvider()
        action = Action(capability_id="test.mock", parameters={"message": "hello"})

        result = await executor.execute(action, provider)

        assert result.success is True
        assert result.output == {"result": "Echo: hello"}
        assert result.error is None
        assert result.duration_ms is not None
        assert result.capability_id == "test.mock"

        await bus.stop()

    @pytest.mark.asyncio
    async def test_governance_denied(self):
        """Governance denial prevents execution."""
        bus = EventBus()
        await bus.start()
        governance = GovernanceGate()
        governance.deny_capability("test.mock")

        executor = CapabilityExecutor(bus, governance)
        provider = MockCapabilityProvider()
        action = Action(capability_id="test.mock", parameters={"message": "hello"})

        result = await executor.execute(action, provider)

        assert result.success is False
        assert "governance" in result.error.lower()

        await bus.stop()

    @pytest.mark.asyncio
    async def test_validation_error(self):
        """Validation errors are caught and reported."""
        bus = EventBus()
        await bus.start()
        governance = GovernanceGate()
        executor = CapabilityExecutor(bus, governance)

        provider = FailingCapabilityProvider()
        action = Action(capability_id="test.failing", parameters={})

        result = await executor.execute(action, provider)

        assert result.success is False
        assert "Validation error" in result.error

        await bus.stop()

    @pytest.mark.asyncio
    async def test_events_published(self):
        """Executor publishes lifecycle events."""
        bus = EventBus()
        await bus.start()
        governance = GovernanceGate()
        executor = CapabilityExecutor(bus, governance)

        received_events: list[EventType] = []

        async def capture(event: Event):
            received_events.append(event.event_type)

        bus.subscribe(EventType.ACTION_VALIDATED, capture)
        bus.subscribe(EventType.ACTION_STARTED, capture)
        bus.subscribe(EventType.ACTION_COMPLETED, capture)

        provider = MockCapabilityProvider()
        action = Action(capability_id="test.mock", parameters={"message": "hello"})

        await executor.execute(action, provider)

        assert EventType.ACTION_VALIDATED in received_events
        assert EventType.ACTION_STARTED in received_events
        assert EventType.ACTION_COMPLETED in received_events

        await bus.stop()

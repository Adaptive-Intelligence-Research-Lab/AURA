"""Tests for the CapabilityExecutor."""

import pytest

from aura.execution.executor import CapabilityExecutor
from aura.models.actions import Action
from aura.models.capabilities import (
    CapabilityMetadata,
    CapabilityProvider,
    RiskLevel,
)
from aura.models.events import Event, EventType
from aura.runtime.event_bus.bus import EventBus
from aura.runtime.governance.gate import GovernanceGate


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
        assert result.capability_id == "test.mock"
        assert result.execution_id is not None

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
        """Executor publishes lifecycle events in correct order."""
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

        assert received_events == [
            EventType.ACTION_VALIDATED,
            EventType.ACTION_STARTED,
            EventType.ACTION_COMPLETED,
        ]

        await bus.stop()

    @pytest.mark.asyncio
    async def test_governance_denial_publishes_failure_event(self):
        """Governance denial produces ACTION_FAILED event."""
        bus = EventBus()
        await bus.start()
        governance = GovernanceGate()
        governance.deny_capability("test.mock")
        executor = CapabilityExecutor(bus, governance)

        received_events: list[Event] = []

        async def capture(event: Event):
            received_events.append(event)

        bus.subscribe(EventType.ACTION_FAILED, capture)

        provider = MockCapabilityProvider()
        action = Action(capability_id="test.mock", parameters={"message": "hello"})

        await executor.execute(action, provider)

        assert len(received_events) == 1
        assert "governance" in received_events[0].payload["error"].lower()

        await bus.stop()

    @pytest.mark.asyncio
    async def test_correlation_id_propagates(self):
        """All events share the action's correlation_id."""
        bus = EventBus()
        await bus.start()
        governance = GovernanceGate()
        executor = CapabilityExecutor(bus, governance)

        received_correlations = []

        async def capture(event: Event):
            received_correlations.append(event.correlation_id)

        for et in (EventType.ACTION_VALIDATED, EventType.ACTION_STARTED, EventType.ACTION_COMPLETED):
            bus.subscribe(et, capture)

        provider = MockCapabilityProvider()
        action = Action(capability_id="test.mock", parameters={"message": "hello"})

        await executor.execute(action, provider)

        assert len(received_correlations) == 3
        assert all(c == action.correlation_id for c in received_correlations)

        await bus.stop()

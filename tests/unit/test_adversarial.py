"""Adversarial tests — §41 failure scenarios (requirement #9)."""
import asyncio
from uuid import uuid4

import pytest

from aura.execution.providers import EchoProvider
from aura.models.actions import Action
from aura.models.capabilities import (
    CapabilityMetadata,
    CapabilityProvider,
    RiskLevel,
)
from aura.models.events import Event, EventType
from aura.models.state import ActionState, StateTransitionError
from aura.runtime.event_bus.bus import EventBus
from aura.runtime.kernel import AURARuntime
from aura.runtime.state.manager import StateManager

# --- Providers for adversarial tests ---


class ProviderThatRaisesOnExecute(CapabilityProvider):
    @property
    def metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            id="test.raises",
            version="1.0.0",
            name="Raises",
            description="Fails on execute",
            input_schema={},
            output_schema={},
            permissions=[],
            risk_level=RiskLevel.LOW,
        )

    def validate(self, parameters: dict) -> dict:
        return parameters

    async def execute(self, parameters: dict) -> dict:
        raise RuntimeError("Provider deliberately failed")


class ProviderThatRaisesOnValidate(CapabilityProvider):
    @property
    def metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            id="test.bad_validate",
            version="1.0.0",
            name="BadValidate",
            description="Fails on validate",
            input_schema={},
            output_schema={},
            permissions=[],
            risk_level=RiskLevel.LOW,
        )

    def validate(self, parameters: dict) -> dict:
        raise ValueError("Validation deliberately failed")

    async def execute(self, parameters: dict) -> dict:
        return {}


# --- 1. Provider failure ---


class TestAdversarialProviderFailure:
    @pytest.mark.asyncio
    async def test_provider_execution_failure(self):
        """Provider raising during execute produces ACTION_FAILED and failure result."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()
        await runtime.register_capability(ProviderThatRaisesOnExecute())

        action = Action(capability_id="test.raises", parameters={})
        result = await runtime.execute(action)

        assert result.success is False
        assert "Execution error" in result.error
        assert runtime.get_state(str(action.id)) == ActionState.FAILED
        await runtime.stop()

    @pytest.mark.asyncio
    async def test_provider_validation_failure(self):
        """Provider raising during validate produces ACTION_FAILED."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()
        await runtime.register_capability(ProviderThatRaisesOnValidate())

        action = Action(capability_id="test.bad_validate", parameters={})
        result = await runtime.execute(action)

        assert result.success is False
        assert "Validation error" in result.error
        assert runtime.get_state(str(action.id)) == ActionState.FAILED
        await runtime.stop()


# --- 2. Governance denial ---


class TestAdversarialGovernanceDenial:
    @pytest.mark.asyncio
    async def test_denied_action_never_reaches_provider(self):
        """Governance denial blocks execution and publishes failure event."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        provider_executed = False

        class SpyProvider(CapabilityProvider):
            @property
            def metadata(self) -> CapabilityMetadata:
                return CapabilityMetadata(
                    id="test.spy",
                    version="1.0.0",
                    name="Spy",
                    description="Tracks if execute was called",
                    input_schema={},
                    output_schema={},
                    permissions=[],
                    risk_level=RiskLevel.LOW,
                )

            def validate(self, parameters: dict) -> dict:
                return parameters

            async def execute(self, parameters: dict) -> dict:
                nonlocal provider_executed
                provider_executed = True
                return {}

        await runtime.register_capability(SpyProvider())
        runtime.governance.deny_capability("test.spy")

        result = await runtime.execute(Action(capability_id="test.spy", parameters={}))

        assert result.success is False
        assert provider_executed is False
        await runtime.stop()


# --- 3. Subscriber failure ---


class TestAdversarialSubscriberFailure:
    @pytest.mark.asyncio
    async def test_failing_subscriber_does_not_break_others(self):
        """One subscriber error does not prevent others from receiving events."""
        bus = EventBus()
        await bus.start()

        good_received = []

        async def failing_handler(event: Event) -> None:
            raise RuntimeError("Subscriber exploded")

        async def good_handler(event: Event) -> None:
            good_received.append(event)

        bus.subscribe(EventType.ACTION_CREATED, failing_handler)
        bus.subscribe(EventType.ACTION_CREATED, good_handler)

        await bus.publish(
            Event(event_type=EventType.ACTION_CREATED, source="test", payload={})
        )

        assert len(good_received) == 1
        await bus.stop()

    @pytest.mark.asyncio
    async def test_multiple_failing_subscribers_isolation(self):
        """Multiple failing subscribers don't break the bus."""
        bus = EventBus()
        await bus.start()

        good_received = []

        async def fail_a(event: Event) -> None:
            raise RuntimeError("A failed")

        async def fail_b(event: Event) -> None:
            raise ValueError("B failed")

        async def good_handler(event: Event) -> None:
            good_received.append(event)

        bus.subscribe(EventType.ACTION_COMPLETED, fail_a)
        bus.subscribe(EventType.ACTION_COMPLETED, good_handler)
        bus.subscribe(EventType.ACTION_COMPLETED, fail_b)

        await bus.publish(
            Event(event_type=EventType.ACTION_COMPLETED, source="test", payload={})
        )

        assert len(good_received) == 1
        await bus.stop()


# --- 4. Invalid state transition ---


class TestAdversarialInvalidTransition:
    @pytest.mark.asyncio
    async def test_invalid_state_transition_raises(self):
        """State manager rejects invalid transitions."""
        sm = StateManager()
        action_id = str(uuid4())

        await sm.handle_event(Event(
            event_type=EventType.ACTION_CREATED,
            source="test",
            payload={"action_id": action_id},
        ))

        # CREATED -> COMPLETED is invalid
        with pytest.raises(StateTransitionError):
            await sm.handle_event(Event(
                event_type=EventType.ACTION_COMPLETED,
                source="test",
                payload={"action_id": action_id},
            ))

    @pytest.mark.asyncio
    async def test_completed_is_terminal(self):
        """COMPLETED state cannot transition to any other state."""
        sm = StateManager()
        action_id = str(uuid4())

        for event_type in (
            EventType.ACTION_CREATED,
            EventType.ACTION_VALIDATED,
            EventType.ACTION_STARTED,
            EventType.ACTION_COMPLETED,
        ):
            await sm.handle_event(Event(
                event_type=event_type,
                source="test",
                payload={"action_id": action_id},
            ))

        # COMPLETED -> RUNNING should fail
        with pytest.raises(StateTransitionError):
            await sm.handle_event(Event(
                event_type=EventType.ACTION_STARTED,
                source="test",
                payload={"action_id": action_id},
            ))


# --- 5. Concurrent execution ---


class TestAdversarialConcurrentExecution:
    @pytest.mark.asyncio
    async def test_concurrent_actions_dont_interfere(self):
        """Multiple actions executed concurrently track state independently."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        await runtime.register_capability(EchoProvider())

        actions = [
            Action(capability_id="core.echo", parameters={"message": f"msg{i}"})
            for i in range(10)
        ]
        results = await asyncio.gather(*[runtime.execute(a) for a in actions])

        for i, (action, result) in enumerate(zip(actions, results)):
            assert result.success is True
            assert result.output == {"message": f"msg{i}"}
            assert runtime.get_state(str(action.id)) == ActionState.COMPLETED

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_concurrent_failure_doesnt_affect_others(self):
        """One failing concurrent action doesn't affect others."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        await runtime.register_capability(EchoProvider())
        await runtime.register_capability(ProviderThatRaisesOnExecute())

        actions = [
            Action(capability_id="core.echo", parameters={"message": f"ok{i}"})
            for i in range(5)
        ] + [
            Action(capability_id="test.raises", parameters={})
            for _ in range(3)
        ]

        results = await asyncio.gather(*[runtime.execute(a) for a in actions])

        # First 5 should succeed
        for result in results[:5]:
            assert result.success is True
        # Last 3 should fail
        for result in results[5:]:
            assert result.success is False

        await runtime.stop()


# --- 6. Event ordering ---


class TestAdversarialEventOrdering:
    @pytest.mark.asyncio
    async def test_events_for_same_action_are_ordered(self):
        """Events for a single action arrive in lifecycle order."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        await runtime.register_capability(EchoProvider())

        event_order = []

        async def capture(event: Event) -> None:
            event_order.append(event.event_type)

        for et in (
            EventType.ACTION_CREATED,
            EventType.ACTION_VALIDATED,
            EventType.ACTION_STARTED,
            EventType.ACTION_COMPLETED,
        ):
            runtime.event_bus.subscribe(et, capture)

        await runtime.execute(
            Action(capability_id="core.echo", parameters={"message": "order"})
        )

        expected = [
            EventType.ACTION_CREATED,
            EventType.ACTION_VALIDATED,
            EventType.ACTION_STARTED,
            EventType.ACTION_COMPLETED,
        ]
        assert event_order == expected
        await runtime.stop()

    @pytest.mark.asyncio
    async def test_failure_event_order_on_validation_error(self):
        """Validation failure produces CREATED then FAILED (no COMPLETED)."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        await runtime.register_capability(EchoProvider())

        event_order = []

        async def capture(event: Event) -> None:
            event_order.append(event.event_type)

        runtime.event_bus.subscribe(EventType.ACTION_CREATED, capture)
        runtime.event_bus.subscribe(EventType.ACTION_FAILED, capture)

        # EchoProvider requires 'message' — sending empty params triggers validation failure
        await runtime.execute(
            Action(capability_id="core.echo", parameters={})
        )

        assert EventType.ACTION_CREATED in event_order
        assert EventType.ACTION_FAILED in event_order
        assert EventType.ACTION_COMPLETED not in event_order
        await runtime.stop()

    @pytest.mark.asyncio
    async def test_failure_event_order_on_governance_denial(self):
        """Governance denial produces CREATED then FAILED (no VALIDATED/STARTED/COMPLETED)."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        await runtime.register_capability(EchoProvider())
        runtime.governance.deny_capability("core.echo")

        event_order = []

        async def capture(event: Event) -> None:
            event_order.append(event.event_type)

        for et in (
            EventType.ACTION_CREATED,
            EventType.ACTION_VALIDATED,
            EventType.ACTION_STARTED,
            EventType.ACTION_COMPLETED,
            EventType.ACTION_FAILED,
        ):
            runtime.event_bus.subscribe(et, capture)

        await runtime.execute(
            Action(capability_id="core.echo", parameters={"message": "x"})
        )

        assert event_order == [EventType.ACTION_CREATED, EventType.ACTION_VALIDATED, EventType.ACTION_FAILED]
        await runtime.stop()

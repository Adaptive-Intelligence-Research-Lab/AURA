"""Integration test — full Action → Registry → Governance → Executor → Provider → EventBus → StateManager chain."""
import pytest

from aura.execution.providers import EchoProvider, SystemInfoProvider
from aura.models.actions import Action
from aura.models.events import EventType
from aura.models.state import ActionState
from aura.runtime.kernel import AURARuntime


class TestRuntimeExecutionIntegration:
    @pytest.mark.asyncio
    async def test_full_execution_pipeline(self):
        """Action flows through every component in the correct order."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        await runtime.register_capability(EchoProvider())

        action = Action(capability_id="core.echo", parameters={"message": "integration"})
        result = await runtime.execute(action)

        assert result.success is True
        assert result.output == {"message": "integration"}
        assert runtime.get_state(str(action.id)) == ActionState.COMPLETED

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_governance_denial_produces_failure_event(self):
        """Governance denial publishes ACTION_FAILED and returns failure."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        runtime.governance.deny_capability("core.echo")
        await runtime.register_capability(EchoProvider())

        action = Action(capability_id="core.echo", parameters={"message": "denied"})
        result = await runtime.execute(action)

        assert result.success is False
        assert "governance" in result.error.lower()
        assert runtime.get_state(str(action.id)) == ActionState.FAILED

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_correlation_id_propagates_through_events(self):
        """All events in a lifecycle share the action's correlation_id."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        await runtime.register_capability(EchoProvider())

        action = Action(capability_id="core.echo", parameters={"message": "corr"})
        received_correlations = []

        async def capture(event):
            received_correlations.append(event.correlation_id)

        runtime.event_bus.subscribe(EventType.ACTION_CREATED, capture)
        runtime.event_bus.subscribe(EventType.ACTION_VALIDATED, capture)
        runtime.event_bus.subscribe(EventType.ACTION_STARTED, capture)
        runtime.event_bus.subscribe(EventType.ACTION_COMPLETED, capture)

        await runtime.execute(action)

        assert len(received_correlations) == 4
        assert all(c == action.correlation_id for c in received_correlations)

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_validation_error_through_full_pipeline(self):
        """Provider validation error flows through the full pipeline."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        await runtime.register_capability(EchoProvider())

        # EchoProvider requires 'message' parameter
        action = Action(capability_id="core.echo", parameters={})
        result = await runtime.execute(action)

        assert result.success is False
        assert "Validation error" in result.error
        assert runtime.get_state(str(action.id)) == ActionState.FAILED

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_multiple_capabilities_independent(self):
        """Multiple capabilities can be registered and executed."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        await runtime.register_capability(EchoProvider())
        await runtime.register_capability(SystemInfoProvider())

        r1 = await runtime.execute(
            Action(capability_id="core.echo", parameters={"message": "hi"})
        )
        assert r1.success
        assert r1.output == {"message": "hi"}

        r2 = await runtime.execute(
            Action(capability_id="core.system_info", parameters={})
        )
        assert r2.success
        assert "platform" in r2.output

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_event_ordering_for_single_action(self):
        """Events for a single action arrive in lifecycle order."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        await runtime.register_capability(EchoProvider())

        event_order = []

        async def capture(event):
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

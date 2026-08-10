"""Tests for the Runtime Kernel (AURARuntime)."""

import pytest

from aura.models.actions import Action
from aura.models.capabilities import (
    CapabilityMetadata,
    CapabilityProvider,
    RiskLevel,
)
from aura.models.state import ActionState
from aura.runtime.kernel import AURARuntime


class EchoProvider(CapabilityProvider):
    @property
    def metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            id="core.echo",
            version="1.0.0",
            name="Echo",
            description="Echoes input",
            input_schema={"message": {"type": "string"}},
            output_schema={"echo": {"type": "string"}},
            permissions=[],
            risk_level=RiskLevel.MINIMAL,
        )

    def validate(self, parameters: dict) -> dict:
        return parameters

    async def execute(self, parameters: dict) -> dict:
        return {"echo": parameters.get("message", "")}


class TestAURARuntime:
    """Tests for AURARuntime."""

    @pytest.mark.asyncio
    async def test_initialize_and_start(self):
        """Runtime initializes and starts cleanly."""
        runtime = AURARuntime()
        await runtime.initialize()
        assert runtime._initialized is True
        await runtime.start()
        assert runtime._started is True
        await runtime.stop()
        assert runtime._initialized is False

    @pytest.mark.asyncio
    async def test_register_and_execute(self):
        """Register capability, execute action."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        provider = EchoProvider()
        await runtime.register_capability(provider)

        action = Action(
            capability_id="core.echo",
            parameters={"message": "hello"}
        )
        result = await runtime.execute(action)

        assert result.success is True
        assert result.output == {"echo": "hello"}

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_execute_unregistered_capability(self):
        """Executing unregistered capability raises ValueError."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        action = Action(
            capability_id="nonexistent.cap",
            parameters={}
        )

        with pytest.raises(ValueError, match="not registered"):
            await runtime.execute(action)

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_execute_without_start(self):
        """Executing without start raises RuntimeError."""
        runtime = AURARuntime()

        action = Action(
            capability_id="core.echo",
            parameters={"message": "test"}
        )

        with pytest.raises(RuntimeError, match="not started"):
            await runtime.execute(action)

    @pytest.mark.asyncio
    async def test_double_initialize_raises(self):
        """Initializing twice raises RuntimeError."""
        runtime = AURARuntime()
        await runtime.initialize()

        with pytest.raises(RuntimeError, match="already initialized"):
            await runtime.initialize()

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_start_without_initialize_raises(self):
        """Starting without initialize raises RuntimeError."""
        runtime = AURARuntime()

        with pytest.raises(RuntimeError, match="Call initialize"):
            await runtime.start()

    @pytest.mark.asyncio
    async def test_state_tracking_through_kernel(self):
        """Runtime tracks action state through events."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        provider = EchoProvider()
        await runtime.register_capability(provider)

        action = Action(
            capability_id="core.echo",
            parameters={"message": "test"}
        )
        await runtime.execute(action)

        action_id = str(action.id)
        state = runtime.get_state(action_id)
        assert state == ActionState.COMPLETED

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_governance_denial_through_kernel(self):
        """Governance denial is enforced through the runtime."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        runtime.governance.deny_capability("core.echo")
        await runtime.register_capability(EchoProvider())

        action = Action(
            capability_id="core.echo",
            parameters={"message": "test"}
        )
        result = await runtime.execute(action)

        assert result.success is False
        assert "governance" in result.error.lower()

        await runtime.stop()

    @pytest.mark.asyncio
    async def test_health(self):
        """health() returns correct status."""
        runtime = AURARuntime()
        await runtime.initialize()
        await runtime.start()

        health = await runtime.health()
        assert health["status"] == "ready"
        assert health["started"] is True
        assert health["initialized"] is True
        assert "runtime_id" in health

        await runtime.stop()

        health = await runtime.health()
        assert health["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """async with AURARuntime() works."""
        async with AURARuntime() as runtime:
            await runtime.register_capability(EchoProvider())
            result = await runtime.execute(
                Action(capability_id="core.echo", parameters={"message": "ctx"})
            )
            assert result.success is True
            assert result.output == {"echo": "ctx"}

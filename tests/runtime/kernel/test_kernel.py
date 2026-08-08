"""Tests for the Runtime Kernel."""

import pytest

from aura.models.actions import Action
from aura.models.capabilities import (
    CapabilityMetadata,
    CapabilityProvider,
    RiskLevel,
)
from aura.models.state import ActionState
from aura.runtime.kernel.kernel import RuntimeKernel


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


class TestRuntimeKernel:
    """Tests for RuntimeKernel."""

    @pytest.mark.asyncio
    async def test_kernel_lifecycle(self):
        """Kernel starts and stops cleanly."""
        kernel = RuntimeKernel()
        await kernel.start()
        assert kernel._initialized is True
        await kernel.stop()
        assert kernel._initialized is False

    @pytest.mark.asyncio
    async def test_register_and_execute(self):
        """End-to-end: register capability, execute action."""
        kernel = RuntimeKernel()
        await kernel.start()

        provider = EchoProvider()
        await kernel.register_capability(provider)

        action = Action(
            capability_id="core.echo",
            parameters={"message": "hello"}
        )
        result = await kernel.execute(action)

        assert result.success is True
        assert result.output == {"echo": "hello"}

        await kernel.stop()

    @pytest.mark.asyncio
    async def test_execute_unregistered_capability(self):
        """Executing unregistered capability raises ValueError."""
        kernel = RuntimeKernel()
        await kernel.start()

        action = Action(
            capability_id="nonexistent.cap",
            parameters={}
        )

        with pytest.raises(ValueError, match="not registered"):
            await kernel.execute(action)

        await kernel.stop()

    @pytest.mark.asyncio
    async def test_execute_without_start(self):
        """Executing without starting raises RuntimeError."""
        kernel = RuntimeKernel()

        action = Action(
            capability_id="core.echo",
            parameters={"message": "test"}
        )

        with pytest.raises(RuntimeError, match="not started"):
            await kernel.execute(action)

    @pytest.mark.asyncio
    async def test_double_start_raises(self):
        """Starting twice raises RuntimeError."""
        kernel = RuntimeKernel()
        await kernel.start()

        with pytest.raises(RuntimeError, match="already initialized"):
            await kernel.start()

        await kernel.stop()

    @pytest.mark.asyncio
    async def test_state_tracking_through_kernel(self):
        """Kernel tracks action state through events."""
        kernel = RuntimeKernel()
        await kernel.start()

        provider = EchoProvider()
        await kernel.register_capability(provider)

        action = Action(
            capability_id="core.echo",
            parameters={"message": "test"}
        )
        await kernel.execute(action)

        action_id = str(action.id)
        state = kernel.get_state(action_id)
        assert state == ActionState.COMPLETED

        await kernel.stop()

    @pytest.mark.asyncio
    async def test_governance_denial_through_kernel(self):
        """Governance denial is enforced through the kernel."""
        kernel = RuntimeKernel()
        await kernel.start()

        kernel.governance.deny_capability("core.echo")
        await kernel.register_capability(EchoProvider())

        action = Action(
            capability_id="core.echo",
            parameters={"message": "test"}
        )
        result = await kernel.execute(action)

        assert result.success is False
        assert "governance" in result.error.lower()

        await kernel.stop()

"""E2E test — §35.3 primary acceptance test."""
import pytest

from aura.execution.providers import EchoProvider, SleepProvider, SystemInfoProvider
from aura.models.actions import Action
from aura.models.state import ActionState
from aura.runtime.kernel import AURARuntime


class TestKernelLifecycleE2E:
    @pytest.mark.asyncio
    async def test_complete_lifecycle(self):
        """§43 Definition of Done: start → register → execute → verify → shutdown."""
        async with AURARuntime() as runtime:
            await runtime.register_capability(EchoProvider())
            result = await runtime.execute(
                Action(capability_id="core.echo", parameters={"message": "Hello AURA"})
            )
            assert result.success is True
            assert result.output == {"message": "Hello AURA"}

    @pytest.mark.asyncio
    async def test_all_three_providers(self):
        """All three v0.1 providers execute successfully."""
        async with AURARuntime() as runtime:
            await runtime.register_capability(EchoProvider())
            await runtime.register_capability(SystemInfoProvider())
            await runtime.register_capability(SleepProvider())

            # core.echo
            r1 = await runtime.execute(
                Action(capability_id="core.echo", parameters={"message": "hi"})
            )
            assert r1.success
            assert r1.output == {"message": "hi"}

            # core.system_info
            r2 = await runtime.execute(
                Action(capability_id="core.system_info", parameters={})
            )
            assert r2.success
            assert "platform" in r2.output
            assert "python_version" in r2.output
            assert "process_id" in r2.output
            assert "runtime_version" in r2.output

            # core.sleep
            r3 = await runtime.execute(
                Action(capability_id="core.sleep", parameters={"duration_ms": 10})
            )
            assert r3.success
            assert r3.output["slept_ms"] == 10

    @pytest.mark.asyncio
    async def test_health_reports_ready(self):
        """health() returns correct status."""
        async with AURARuntime() as runtime:
            health = await runtime.health()
            assert health["status"] == "ready"
            assert health["started"] is True

    @pytest.mark.asyncio
    async def test_action_state_lifecycle_tracked(self):
        """Action state transitions through COMPLETED."""
        async with AURARuntime() as runtime:
            await runtime.register_capability(EchoProvider())
            action = Action(
                capability_id="core.echo", parameters={"message": "track"}
            )
            await runtime.execute(action)
            assert runtime.get_state(str(action.id)) == ActionState.COMPLETED

    @pytest.mark.asyncio
    async def test_unregistered_capability_fails(self):
        """Executing unregistered capability raises ValueError."""
        async with AURARuntime() as runtime:
            with pytest.raises(ValueError, match="not registered"):
                await runtime.execute(
                    Action(capability_id="nonexistent", parameters={})
                )

    @pytest.mark.asyncio
    async def test_governance_denial_blocks_execution(self):
        """Governance denial blocks execution and tracks FAILED state."""
        async with AURARuntime() as runtime:
            await runtime.register_capability(EchoProvider())
            runtime.governance.deny_capability("core.echo")

            action = Action(
                capability_id="core.echo", parameters={"message": "denied"}
            )
            result = await runtime.execute(action)

            assert result.success is False
            assert runtime.get_state(str(action.id)) == ActionState.FAILED

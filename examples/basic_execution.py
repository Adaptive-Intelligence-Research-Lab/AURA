"""
AURA v0.1 — Basic Execution Example

Demonstrates the Definition of Done (§43):
  async with AURARuntime() as runtime:
      result = await runtime.execute(
          Action(capability_id="core.echo", parameters={"message": "Hello AURA"})
      )
      assert result.success
"""
import asyncio

from aura.execution.providers import EchoProvider, SleepProvider, SystemInfoProvider
from aura.models.actions import Action
from aura.runtime.kernel import AURARuntime


async def main() -> None:
    async with AURARuntime() as runtime:
        # Register v0.1 providers
        await runtime.register_capability(EchoProvider())
        await runtime.register_capability(SystemInfoProvider())
        await runtime.register_capability(SleepProvider())

        # Execute core.echo
        result = await runtime.execute(
            Action(
                capability_id="core.echo",
                parameters={"message": "Hello AURA"},
            )
        )
        print(f"Echo result: {result.output}")
        assert result.success

        # Execute core.system_info
        result = await runtime.execute(
            Action(capability_id="core.system_info", parameters={})
        )
        print(f"System info: {result.output}")

        # Execute core.sleep
        result = await runtime.execute(
            Action(capability_id="core.sleep", parameters={"duration_ms": 100})
        )
        print(f"Sleep result: {result.output}")

        # Check health
        health = await runtime.health()
        print(f"Health: {health}")


if __name__ == "__main__":
    asyncio.run(main())

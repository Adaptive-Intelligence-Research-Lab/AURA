"""
Main entry point for AURA Runtime Core v0.1.

This provides a demonstration entry point.
Full CLI will be implemented in later phases.
"""
import asyncio
import sys

from aura.execution.providers import EchoProvider
from aura.models.actions import Action
from aura.runtime.kernel import AURARuntime


async def main() -> int:
    async with AURARuntime() as runtime:
        await runtime.register_capability(EchoProvider())
        result = await runtime.execute(
            Action(
                capability_id="core.echo",
                parameters={"message": "Hello AURA"},
            )
        )
        print(f"Result: {result.output}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

"""
Experiment E-001: Capability Independence

Question:
    Can a capability/action abstraction support independent execution
    providers without modifying the Runtime Kernel?

Hypothesis:
    If the Capability Provider Contract is sufficiently stable,
    new capabilities can be added without modifying kernel
    orchestration logic.

Method:
    1. Implement core.echo, core.system_info, core.sleep
    2. Register all three
    3. Execute all three
    4. Inspect kernel code for provider-specific branching
    5. Verify no provider-specific conditionals exist in kernel

Environment:
    Python 3.11.0, AURA v0.1, single-process, Windows

Expected Result:
    All three providers execute successfully.
    Kernel code contains zero provider-specific conditionals.

Observed Result:
    [To be filled after execution]

Evidence:
    [To be filled after execution]

Limitations:
    - Only 3 providers tested
    - Larger provider counts not evaluated
    - No stress testing under high concurrency

Conclusion:
    [To be filled after execution]
"""
from __future__ import annotations

import asyncio
import inspect
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from aura.execution.providers import EchoProvider, SleepProvider, SystemInfoProvider
from aura.models.actions import Action
from aura.runtime.kernel import AURARuntime


PROVIDER_SPECIFIC_PATTERNS = [
    "core.echo",
    "core.system_info",
    "core.sleep",
    "EchoProvider",
    "SystemInfoProvider",
    "SleepProvider",
]


async def run_experiment() -> dict:
    """Execute E-001 and return results."""
    results = {
        "hypothesis": "New capabilities can be added without modifying kernel",
        "providers_tested": [],
        "executions": [],
        "kernel_inspection": {},
    }

    # Step 1-3: Register and execute all three providers
    providers = [EchoProvider(), SystemInfoProvider(), SleepProvider()]
    test_cases = [
        ("core.echo", {"message": "test"}),
        ("core.system_info", {}),
        ("core.sleep", {"duration_ms": 1}),
    ]

    async with AURARuntime() as runtime:
        for provider in providers:
            await runtime.register_capability(provider)
            results["providers_tested"].append(provider.metadata.id)

        for cap_id, params in test_cases:
            action = Action(capability_id=cap_id, parameters=params)
            result = await runtime.execute(action)
            results["executions"].append({
                "capability_id": cap_id,
                "success": result.success,
                "output_keys": list(result.output.keys()) if result.output else [],
            })

    # Step 4-5: Inspect kernel code
    kernel_source = inspect.getsource(AURARuntime)
    found_patterns = []
    for pattern in PROVIDER_SPECIFIC_PATTERNS:
        if pattern in kernel_source:
            found_patterns.append(pattern)

    results["kernel_inspection"] = {
        "source_lines": len(kernel_source.splitlines()),
        "provider_specific_patterns_found": found_patterns,
        "has_provider_branching": len(found_patterns) > 0,
    }

    return results


def main() -> None:
    """Run E-001 and print results."""
    results = asyncio.run(run_experiment())

    print("=" * 60)
    print("Experiment E-001: Capability Independence")
    print("=" * 60)
    print()
    print("Hypothesis: New capabilities can be added without modifying kernel")
    print()
    print("Providers tested:", results["providers_tested"])
    print()
    print("Executions:")
    for ex in results["executions"]:
        print(f"  {ex['capability_id']}: success={ex['success']}, output_keys={ex['output_keys']}")
    print()
    print("Kernel inspection:")
    ki = results["kernel_inspection"]
    print(f"  Source lines: {ki['source_lines']}")
    print(f"  Provider-specific patterns found: {ki['provider_specific_patterns_found']}")
    print(f"  Has provider branching: {ki['has_provider_branching']}")
    print()

    all_success = all(ex["success"] for ex in results["executions"])
    no_branching = not ki["has_provider_branching"]

    if all_success and no_branching:
        print("RESULT: SUPPORTED — Hypothesis confirmed")
    else:
        print("RESULT: NOT SUPPORTED — See findings above")

    print("=" * 60)


if __name__ == "__main__":
    main()

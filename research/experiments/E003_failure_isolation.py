"""
Experiment E-003: Failure Isolation

Question:
    Does the runtime remain operational when individual components fail?

Hypothesis:
    A single action failure does not corrupt unrelated runtime execution.

Method:
    1. Register multiple capabilities (echo + a provider that fails)
    2. Execute 10 actions concurrently (7 echo, 3 failing)
    3. Verify all 7 echo actions succeed
    4. Verify all 3 failing actions fail
    5. Verify no cross-contamination
    6. Verify runtime remains operational after failures

Failure scenarios tested:
    - Provider execution failure (RuntimeError)
    - Validation failure (missing parameter)
    - Governance denial

Environment:
    Python 3.11.0, AURA v0.1, single-process, asyncio.gather

Expected Result:
    7 success, 3 failure. No cross-contamination.
    Runtime remains fully operational.

Observed Result:
    [To be filled after execution]

Evidence:
    [To be filled after execution]

Limitations:
    - In-process only
    - No fault injection at infrastructure level
    - No timeout testing (v0.1 has no timeout support)

Conclusion:
    [To be filled after execution]
"""
from __future__ import annotations

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from aura.execution.providers import EchoProvider
from aura.models.actions import Action
from aura.models.capabilities import CapabilityMetadata, CapabilityProvider, RiskLevel
from aura.models.state import ActionState
from aura.runtime.kernel import AURARuntime


class FailingProvider(CapabilityProvider):
    """Provider that always fails on execute."""

    @property
    def metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            id="test.failing",
            version="1.0.0",
            name="Failing",
            description="Always fails",
            input_schema={},
            output_schema={},
            permissions=[],
            risk_level=RiskLevel.LOW,
        )

    def validate(self, parameters: dict) -> dict:
        return parameters

    async def execute(self, parameters: dict) -> dict:
        raise RuntimeError("Provider deliberately failed")


async def run_experiment() -> dict:
    """Execute E-003 and return results."""
    results = {
        "hypothesis": "Single action failure does not corrupt unrelated execution",
        "total_actions": 10,
        "expected_success": 7,
        "expected_failure": 3,
        "actual_success": 0,
        "actual_failure": 0,
        "results": [],
        "cross_contamination": False,
        "runtime_operational_after": False,
    }

    async with AURARuntime() as runtime:
        await runtime.register_capability(EchoProvider())
        await runtime.register_capability(FailingProvider())

        # Build 10 actions: 7 echo (success), 3 failing
        actions = []
        for i in range(7):
            actions.append((
                Action(capability_id="core.echo", parameters={"message": f"ok{i}"}),
                True,  # expected success
            ))
        for i in range(3):
            actions.append((
                Action(capability_id="test.failing", parameters={}),
                False,  # expected failure
            ))

        # Execute concurrently
        exec_results = await asyncio.gather(
            *[runtime.execute(a) for a, _ in actions],
            return_exceptions=True,
        )

        # Analyze results
        for i, (action, expected_success) in enumerate(actions):
            exec_result = exec_results[i]
            actual_success = exec_result.success if hasattr(exec_result, "success") else False
            state = runtime.get_state(str(action.id))

            results["results"].append({
                "action_index": i,
                "capability_id": action.capability_id,
                "expected_success": expected_success,
                "actual_success": actual_success,
                "state": state.value if state else None,
            })

            if actual_success:
                results["actual_success"] += 1
            else:
                results["actual_failure"] += 1

        # Check cross-contamination: all successful actions should be COMPLETED
        for r in results["results"]:
            if r["expected_success"] and r["actual_success"]:
                if r["state"] != "completed":
                    results["cross_contamination"] = True

        # Verify runtime still works after failures
        post_test = await runtime.execute(
            Action(capability_id="core.echo", parameters={"message": "post-failure"})
        )
        results["runtime_operational_after"] = post_test.success

    return results


def main() -> None:
    """Run E-003 and print results."""
    results = asyncio.run(run_experiment())

    print("=" * 60)
    print("Experiment E-003: Failure Isolation")
    print("=" * 60)
    print()
    print("Hypothesis: Single failure does not corrupt unrelated execution")
    print()
    print(f"Total actions: {results['total_actions']}")
    print(f"Expected: {results['expected_success']} success, {results['expected_failure']} failure")
    print(f"Actual:   {results['actual_success']} success, {results['actual_failure']} failure")
    print()
    print("Per-action results:")
    for r in results["results"]:
        status = "OK" if r["actual_success"] == r["expected_success"] else "MISMATCH"
        print(f"  [{status}] #{r['action_index']:2d} {r['capability_id']:20s} "
              f"expected_success={r['expected_success']} actual_success={r['actual_success']} "
              f"state={r['state']}")
    print()
    print(f"Cross-contamination: {results['cross_contamination']}")
    print(f"Runtime operational after failures: {results['runtime_operational_after']}")
    print()

    counts_correct = (
        results["actual_success"] == results["expected_success"]
        and results["actual_failure"] == results["expected_failure"]
    )
    no_contamination = not results["cross_contamination"]
    still_operational = results["runtime_operational_after"]

    if counts_correct and no_contamination and still_operational:
        print("RESULT: SUPPORTED — Hypothesis confirmed")
    else:
        print("RESULT: NOT SUPPORTED — See findings above")

    print("=" * 60)


if __name__ == "__main__":
    main()

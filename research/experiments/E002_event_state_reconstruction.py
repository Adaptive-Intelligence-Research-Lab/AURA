"""
Experiment E-002: Event/State Reconstruction

Question:
    Can runtime behavior be reconstructed entirely from events and state?

Hypothesis:
    If all significant lifecycle transitions generate structured events,
    an execution timeline can be reconstructed without inspecting
    provider internals.

Method:
    1. Execute an action through the full pipeline
    2. Capture all events with timestamps and correlation_id
    3. Reconstruct the timeline from event payloads
    4. Compare with actual state transitions
    5. Verify timestamps are monotonically increasing
    6. Verify correlation_id is consistent

Environment:
    Python 3.11.0, AURA v0.1, single-process, Windows

Expected Result:
    Given an action_id, reconstruct:
    Created -> Validated -> Started -> Completed
    with timestamps and correlation identifiers.

Observed Result:
    [To be filled after execution]

Evidence:
    [To be filled after execution]

Limitations:
    - Single-process only
    - No distributed tracing
    - Clock resolution limited to system clock

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
from aura.models.events import Event, EventType
from aura.runtime.kernel import AURARuntime


async def run_experiment() -> dict:
    """Execute E-002 and return results."""
    results = {
        "hypothesis": "Runtime behavior reconstructible from events and state",
        "events_captured": [],
        "timeline": [],
        "correlation_consistent": False,
        "timestamps_monotonic": False,
        "state_reconstruction": {},
    }

    async with AURARuntime() as runtime:
        await runtime.register_capability(EchoProvider())

        captured_events: list[Event] = []

        async def capture(event: Event) -> None:
            captured_events.append(event)

        for et in (
            EventType.ACTION_CREATED,
            EventType.ACTION_VALIDATED,
            EventType.ACTION_STARTED,
            EventType.ACTION_COMPLETED,
            EventType.ACTION_FAILED,
        ):
            runtime.event_bus.subscribe(et, capture)

        action = Action(
            capability_id="core.echo",
            parameters={"message": "reconstruct me"},
        )
        result = await runtime.execute(action)

        # Step 2: Format captured events
        for event in captured_events:
            results["events_captured"].append({
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "correlation_id": str(event.correlation_id),
                "source": event.source,
                "action_id": event.payload.get("action_id"),
            })

        # Step 3: Reconstruct timeline
        results["timeline"] = [e["event_type"] for e in results["events_captured"]]

        # Step 4: Verify correlation_id consistency
        correlation_ids = {e["correlation_id"] for e in results["events_captured"]}
        results["correlation_consistent"] = len(correlation_ids) == 1

        # Step 5: Verify timestamps are monotonic
        timestamps = [e["timestamp"] for e in results["events_captured"]]
        results["timestamps_monotonic"] = timestamps == sorted(timestamps)

        # Step 6: Verify state reconstruction
        action_id = str(action.id)
        final_state = runtime.get_state(action_id)
        results["state_reconstruction"] = {
            "action_id": action_id,
            "final_state": final_state.value if final_state else None,
            "execution_success": result.success,
        }

    return results


def main() -> None:
    """Run E-002 and print results."""
    results = asyncio.run(run_experiment())

    print("=" * 60)
    print("Experiment E-002: Event/State Reconstruction")
    print("=" * 60)
    print()
    print("Hypothesis: Runtime behavior reconstructible from events/state")
    print()
    print("Events captured:")
    for e in results["events_captured"]:
        print(f"  {e['event_type']:20s} | {e['timestamp'][:19]} | corr={e['correlation_id'][:8]}")
    print()
    print(f"Timeline: {' -> '.join(results['timeline'])}")
    print()
    print(f"Correlation consistent: {results['correlation_consistent']}")
    print(f"Timestamps monotonic: {results['timestamps_monotonic']}")
    print()
    sr = results["state_reconstruction"]
    print(f"Final state: {sr['final_state']}")
    print(f"Execution success: {sr['execution_success']}")
    print()

    all_correct = (
        results["correlation_consistent"]
        and results["timestamps_monotonic"]
        and sr["final_state"] == "completed"
        and len(results["timeline"]) == 4
    )

    if all_correct:
        print("RESULT: SUPPORTED — Hypothesis confirmed")
    else:
        print("RESULT: NOT SUPPORTED — See findings above")

    print("=" * 60)


if __name__ == "__main__":
    main()

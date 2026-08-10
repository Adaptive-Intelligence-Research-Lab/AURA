# AURA v0.1.0 Architectural Retrospective

**Project:** Adaptive Unified Runtime Architecture (AURA)
**Organization:** Adaptive Intelligence Research Lab (AIR Lab)
**Release:** v0.1.0 Runtime Core
**Retrospective Date:** 2026-08-10
**Baseline Commit:** `258b0b0`
**Status:** Research artifact -- not an implementation plan

---

## 1. Executive Summary

AURA v0.1.0 delivered a minimal runtime substrate in approximately 1,086 lines of runtime code across 7 core components, 154 tests, 3 capability providers, and skeleton observability.

The implementation validated several architectural assumptions that were not obvious from the specification alone:

- Capability-oriented runtime design is viable with minimal code.
- Event-driven coordination works without external infrastructure.
- Governance-before-execution is enforceable at the pipeline boundary.
- Simple failure isolation is achievable through structured error handling.

The implementation also revealed assumptions that were wrong or incomplete:

- The kernel lifecycle model in the spec (INITIALIZING, SHUTTING_DOWN) was not implemented. The actual implementation uses boolean flags, which is simpler but less observable.
- Configuration models (AuraConfig) exist in the specification but are never used by the runtime kernel.
- Action policy fields (retry_count, timeout_ms) exist in the data model but are never enforced by the executor.
- The observability layer is a skeleton -- 92 lines of code, none of which are wired into the runtime during normal operation.

The most important finding is that the **observability gap is the primary architectural risk**. Without structured logging, metric export, and trace propagation, the runtime cannot be debugged, monitored, or reasoned about at scale. This should be the first priority for v0.2.

This retrospective is a research artifact. It does not select or implement the next v0.2 component.

---

## 2. What We Intended to Build

The v0.1 implementation specification (AURA-IMPL-001) defined a minimal runtime substrate capable of:

- Representing capabilities and actions as data models
- Registering and resolving capabilities through a registry
- Validating and executing actions through a pipeline
- Enforcing a basic governance boundary (allow/deny)
- Maintaining runtime state independently of execution
- Publishing runtime events for observability
- Isolating subscriber failures
- Exposing execution lifecycle information
- Supporting controlled startup and shutdown
- Executing capabilities without capability-specific logic in the kernel

The specification intentionally excluded advanced reasoning, planning, memory, learning, LLM inference, distributed execution, and production-grade observability.

The goal was to establish a **validated experimental substrate**, not a complete intelligent-agent architecture.

---

## 3. What We Actually Built

### Runtime Components

| Component | File | Lines | Status |
|-----------|------|------:|--------|
| AURARuntime (kernel) | `src/aura/runtime/kernel.py` | 198 | Complete |
| EventBus | `src/aura/runtime/event_bus/bus.py` | 143 | Complete |
| CapabilityExecutor | `src/aura/execution/executor.py` | 174 | Complete |
| StateManager | `src/aura/runtime/state/manager.py` | 203 | Complete |
| GovernanceGate | `src/aura/runtime/governance/gate.py` | 121 | Complete |
| CapabilityRegistry | `src/aura/runtime/registry/capabilities.py` | 155 | Complete |
| Observability (3 files) | `src/aura/observability/` | 92 | Skeleton |
| **Total runtime** | | **~1,086** | |

### Data Models

| Model | File | Purpose |
|-------|------|---------|
| Action | `models/actions.py` | Intent to execute a capability |
| Event | `models/events.py` | Immutable runtime fact |
| Capability | `models/capabilities.py` | Provider metadata and risk level |
| ExecutionResult | `models/execution.py` | Outcome of an execution attempt |
| State | `models/state.py` | Action and kernel state enums |
| Config | `models/config.py` | Runtime configuration (unused) |
| Errors | `models/errors.py` | Structured error types |

### Providers

| Provider | Lines | Purpose |
|----------|------:|---------|
| EchoProvider | 31 | Returns input message |
| SystemInfoProvider | 40 | Returns platform information |
| SleepProvider | 37 | Simulates async work |

### Test Infrastructure

| Category | Count | Coverage |
|----------|------:|----------|
| Unit -- models | 7 files | All model classes |
| Unit -- runtime | 4 files | EventBus, governance, state, kernel |
| Unit -- execution | 2 files | Executor, providers |
| Unit -- observability | 2 files | Metrics, tracing |
| Unit -- adversarial | 18 tests | 6 failure classes |
| Integration | 6 tests | Full pipeline |
| E2E | 6 tests | Kernel lifecycle |
| **Total** | **154** | |

### What the Numbers Mean

- 1,086 lines of runtime code is small. A single developer can hold the entire runtime in working memory.
- 154 tests against 1,086 lines is a test-to-code ratio of approximately 1:7 (counting test files as proportional to their subject files). This is adequate for a prototype.
- 3 providers in approximately 108 total lines demonstrates that adding capabilities is low-effort.
- 92 lines of observability code -- none wired into the runtime -- is the most significant gap.

---

## 4. Validated Architectural Assumptions

The following assumptions held under implementation:

### 4.1 Capability Independence Is Viable

**Evidence:** Experiment E-001. The kernel source contains zero provider-specific branching patterns. All 3 providers execute through the same generic pipeline in executor.py. The kernel does not import or reference any concrete provider class.

**Implication:** The Open/Closed Principle applies to this runtime. New capabilities can be added through registration without modifying kernel code.

### 4.2 Event-Driven Coordination Works Without Infrastructure

**Evidence:** The EventBus achieves approximately 263K events/sec with 4.4us p50 latency using only Python asyncio. No Redis, Kafka, or external broker is required.

**Implication:** In-process async publish/subscribe is sufficient for a single-process runtime. External infrastructure is a scaling concern, not an architectural requirement.

### 4.3 State and Execution Should Remain Separate

**Evidence:** StateManager tracks action lifecycle independently from CapabilityExecutor. The executor does not read or write state directly -- it publishes events that the state manager observes. This separation is clean in the code.

**Implication:** The state layer can evolve (persistence, recovery, adaptive behavior) without modifying the execution pipeline.

### 4.4 Governance-Before-Execution Is Enforceable

**Evidence:** GovernanceGate.evaluate() is called in executor.py before any provider code runs. When governance denies an action, the provider's execute() method is never called (verified by spy in adversarial tests).

**Implication:** The execution pipeline has a structural safety boundary. Future cognitive systems can submit actions through this boundary without bypassing governance.

### 4.5 Subscriber Failure Isolation Works

**Evidence:** EventBus wraps each subscriber call in try/except. A failing subscriber is logged and skipped; subsequent subscribers still receive the event. Tested with RuntimeError, ValueError, and multiple simultaneous failures.

**Implication:** Observability subscribers (future metrics, logging, tracing) cannot crash the runtime by failing.

---

## 5. Invalidated or Weak Assumptions

The following assumptions were wrong or incomplete:

### 5.1 Kernel Lifecycle States

**Specification defined:** CREATED -> INITIALIZING -> READY -> EXECUTING -> READY -> SHUTTING_DOWN -> STOPPED

**Implementation:** Two boolean flags (_initialized, _started). INITIALIZING and SHUTTING_DOWN are never represented. EXECUTING is not tracked at the kernel level.

**Impact:** The kernel cannot report its own lifecycle state to external observers. There is no way to distinguish "initializing" from "ready" from the outside. This is a meaningful observability gap.

### 5.2 Configuration Model Is Unused

**Specification defined:** AuraConfig with EventBusConfig, GovernanceConfig, ExecutionConfig, ObservabilityConfig.

**Implementation:** AuraConfig exists in models/config.py but is never passed to or used by AURARuntime. The kernel instantiates all components with defaults.

**Impact:** Runtime behavior is not configurable without code changes. This is acceptable for v0.1 but must change before v0.2.

### 5.3 Action Policy Fields Are Unenforced

**Specification defined:** ActionPolicy with 	imeout_ms, etry_count, max_retries.

**Implementation:** ActionPolicy exists in models/actions.py but the executor never reads 	imeout_ms or etry_count. Actions run without timeout and without retry.

**Impact:** The data model promises capabilities that the executor does not deliver. This creates a false sense of configurability.

### 5.4 Assert-Based Access Guards

**Implementation detail:** AURARuntime uses ssert self._event_bus is not None to access components after initialization. Under python -O, these assertions are stripped, and the code will raise AttributeError instead of a meaningful error.

**Impact:** Low risk in practice (v0.1 is not deployed with -O), but this is an implementation shortcut that should be replaced.

### 5.5 Unbounded State Growth

**Implementation detail:** StateManager._action_states is a plain dict[str, ActionState] with no eviction policy. Every executed action adds an entry that is never removed.

**Impact:** Memory grows linearly with the number of executed actions. For a long-running runtime, this is a memory leak. The kernel's stop() method does not clear this state.

---

## 6. Runtime Kernel Findings

### What Worked Well

The composition root pattern is effective. AURARuntime wires together EventBus, StateManager, GovernanceGate, CapabilityRegistry, and CapabilityExecutor in initialize(). This makes the dependency graph explicit and the components individually testable.

The async context manager (__aenter__/__aexit__) provides clean resource management. The E2E tests confirm this pattern works as intended.

The public API is minimal: initialize(), start(), execute(), health(), stop(). This is easy to understand and teach.

### What Became More Complex Than Expected

The execute() method in the kernel performs three distinct operations: (1) resolve the capability from the registry, (2) publish ACTION_CREATED, (3) delegate to the executor. This means the kernel knows about both the registry and executor internals, creating a two-layer dependency. A cleaner design would have the kernel only call executor.execute(action), with the executor handling resolution internally.

The hardcoded event type subscription list (lines 112-123 of kernel.py) iterates over nine EventType values. Adding a new event type requires modifying this list. This violates the Open/Closed Principle and should be replaced with automatic subscription or a subscriber registry.

### Coupling That Appeared During Implementation

| Coupling Point | Location | Severity |
|----------------|----------|----------|
| Kernel instantiates concrete EventBus | kernel.py:initialize() | High -- no DI |
| Kernel instantiates concrete StateManager | kernel.py:initialize() | High -- no DI |
| Kernel instantiates concrete GovernanceGate | kernel.py:initialize() | High -- no DI |
| Kernel instantiates concrete CapabilityRegistry | kernel.py:initialize() | High -- no DI |
| Kernel instantiates concrete CapabilityExecutor | kernel.py:initialize() | High -- no DI |
| Hardcoded EventType subscription list | kernel.py:112-123 | Medium -- O/C violation |
| Executor imports EventBus directly | executor.py | Medium -- tight coupling |
| Executor imports GovernanceGate directly | executor.py | Medium -- tight coupling |

The lack of dependency injection is the most significant coupling issue. It makes unit testing harder (you cannot mock dependencies without monkeypatching) and makes the kernel non-configurable.

---

## 7. Event Bus Findings

### Actual Semantics

The EventBus provides:

- **Per-event-type sequential dispatch:** Subscribers for a given event type are awaited one-by-one in registration order. This provides deterministic ordering within a single event type.
- **Publish order:** Sequential publish() calls deliver events in publish order.
- **No global ordering:** Concurrent publish() calls do not guarantee global ordering.
- **Subscriber isolation:** Each subscriber call is wrapped in try/except. Failures are logged and skipped.

These semantics are correct for a v0.1 runtime and align with the specification (AURA-SPEC-003 section 14).

### Ordering Guarantees

| Scenario | Guarantee |
|----------|-----------|
| Single event type, sequential publish | Deterministic order |
| Single event type, concurrent publish | Order not guaranteed |
| Multiple event types, sequential publish | Each type's subscribers see publish order |
| Multiple event types, concurrent publish | No cross-type ordering |

For the v0.1 use case (single-process, sequential action execution), these guarantees are sufficient.

### Failure Isolation

The EventBus isolates subscriber failures at the subscriber level. A failing subscriber is:

1. Caught by try/except
2. Logged with the exception type and message
3. Skipped (subsequent subscribers still receive the event)
4. Not retried

This means:

- A metric subscriber cannot crash the runtime
- A logging subscriber cannot block execution
- A tracing subscriber failure is invisible (logged, not propagated)

**Limitation:** Failed events are lost. There is no dead letter queue, no retry mechanism, no event replay. For a production system, this would need to change. For a v0.1 research prototype, it is acceptable.

### Performance Observations

| Metric | Measured | Interpretation |
|--------|----------|----------------|
| Throughput (1 subscriber) | ~263K eps | Adequate for single-process |
| Throughput (10 subscribers) | ~201K eps | 24% degradation at 10x fanout |
| Throughput (100 subscribers) | ~61K eps | 77% degradation at 100x fanout |
| p50 latency | 4.4 us | Sub-5-microsecond delivery |
| p95 latency | 4.6 us | Tight distribution |
| p99 latency | 4.7 us | Minimal tail latency |

The sequential dispatch model creates a linear scaling bottleneck. Throughput degrades proportionally with subscriber count because each subscriber is awaited before the next. This is the correct trade-off for v0.1 (simplicity over throughput) but would need to change for high-fanout scenarios.

### Limitations of the Current In-Process Design

1. **No backpressure:** If a subscriber is slow, the publisher blocks until all subscribers complete.
2. **No event replay:** Events are not retained after delivery.
3. **No dead letter handling:** Failed events are silently lost.
4. **No priority system:** All subscribers are treated equally.
5. **No wildcard subscriptions:** Subscribers must match exact event types.
6. **No metric integration:** No subscriber count, delivery rate, or error rate tracking.
7. **Single-process only:** No inter-process or network transport.

---

## 8. Capability Architecture Findings

### Does Capability Independence Actually Hold?

**Yes, with evidence.** Experiment E-001 verified this by:

1. Registering 3 providers (core.echo, core.system_info, core.sleep)
2. Executing all 3 through the runtime
3. Inspecting the kernel source for provider-specific branching patterns

Result: Zero provider-specific patterns found. The kernel contains no if/else branches that reference specific provider names or classes. All providers execute through the same generic pipeline in executor.py.

### What Was Required to Add a Capability

Adding each of the 3 providers required:

| Step | Effort |
|------|--------|
| Implement CapabilityProvider subclass | 31-40 lines per provider |
| Define metadata (capability_id, risk_level, parameters) | Inline in provider class |
| Implement alidate_parameters() | 5-10 lines |
| Implement execute() | 5-15 lines |
| Register via untime.register_provider() | 1 line |

No kernel code was modified. No registry code was modified. No executor code was modified. The entire process is additive.

### Did the Kernel Remain Capability-Agnostic?

**Yes.** The kernel's execute() method:

1. Receives an Action (which contains capability_id)
2. Resolves the provider from the registry
3. Publishes ACTION_CREATED
4. Delegates to the executor

The kernel never imports, references, or branches on specific capability types. It treats all capabilities as opaque identifiers that resolve to providers.

**Caveat:** The kernel does know about the registry and executor. A future design might move resolution into the executor, making the kernel even more agnostic. But for v0.1, the current separation is adequate.

---

## 9. State and Recovery Findings

### Is the Current State Model Sufficient?

For v0.1, yes. The state model provides:

- 7 action states: CREATED, VALIDATED, QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED
- 7 kernel states: CREATED, INITIALIZING, READY, EXECUTING, RECOVERING, SHUTTING_DOWN, STOPPED
- Valid transition enforcement via VALID_TRANSITIONS map
- Event-driven state updates (state manager subscribes to EventBus)

The model correctly represents the v0.1 lifecycle and rejects invalid transitions (verified by adversarial tests).

### What Information Is Missing for Recovery

| Missing Information | Impact |
|---------------------|--------|
| Event history | Cannot replay actions to reconstruct state |
| Action parameters | Cannot re-execute a failed action |
| Provider execution timing | Cannot diagnose slow providers |
| Resource consumption | Cannot detect memory or CPU exhaustion |
| Error context (stack traces) | Cannot diagnose root cause of failures |
| Action lineage | Cannot trace parent-child action relationships |

Without this information, the runtime cannot recover from process-level failure. State is in-memory only and is lost on restart.

### What Information Is Missing for Future Adaptive Behavior

| Missing Information | Impact |
|---------------------|--------|
| Execution confidence scores | Cannot assess action reliability |
| Resource cost per action | Cannot optimize resource allocation |
| Historical success/failure rates | Cannot learn from past behavior |
| Action similarity metrics | Cannot cluster or categorize actions |
| User feedback signals | Cannot adapt based on outcomes |
| Context snapshots | Cannot correlate actions with environmental state |

These gaps are expected for v0.1. They define the research agenda for future versions.

---

## 10. Governance Findings

### What the Current Governance Gate Can Guarantee

- **Per-capability allow/deny:** The gate evaluates each action against a capability-level policy.
- **Explicit overrides:** Specific capabilities can be allowed or denied regardless of the default policy.
- **Deterministic decisions:** Given the same capability_id and policy, the gate produces the same result.
- **Pre-execution enforcement:** Governance is called before any provider code runs. Denied actions never reach providers.

### What It Cannot Guarantee

| Limitation | Impact |
|------------|--------|
| No rate limiting | A capability can be called unlimited times |
| No risk scoring | All allowed actions are treated equally |
| No context awareness | Governance cannot consider action parameters, time of day, or system state |
| No temporal policies | Cannot enable/disable capabilities based on time |
| No hierarchical policies | Cannot compose policies from multiple sources |
| No audit trail | Governance decisions are not logged |
| No dynamic policy updates | Policies are set at construction time |

### What Will Eventually Require a Richer Policy Model

- Multi-tenant environments (per-user governance)
- Resource-constrained environments (quota enforcement)
- Safety-critical environments (risk-based gating)
- Compliance environments (audit logging, consent management)
- Adaptive environments (learning-based policy evolution)

For v0.1, the simple allow/deny gate is appropriate. The architectural boundary is in place; the policy model just needs to become richer.

---

## 11. Observability Findings

### Can Runtime Behavior Actually Be Reconstructed?

**Partially.** Experiment E-002 demonstrated that a single action's lifecycle can be reconstructed from the event stream:

- ActionCreated -> ActionValidated -> ActionStarted -> ActionCompleted
- Correlation ID is consistent across all events
- Timestamps are monotonically increasing
- Final state matches execution outcome

**What can be reconstructed:**

- Which actions were executed
- What lifecycle events occurred
- The order of events
- The final state of each action
- Which capability was invoked

**What cannot be reconstructed:**

- What the provider actually did (no provider-level tracing)
- How long each phase took (no duration metrics in events)
- What resources were consumed (no resource metrics)
- What errors occurred at the provider level (only final status)
- The full execution context (no context propagation)

### What Information Is Missing from Events and Traces

| Missing Data | Where It Should Appear | Impact |
|--------------|----------------------|--------|
| Provider execution duration | ActionCompleted event | Cannot identify slow providers |
| Provider error details | ActionFailed event | Cannot diagnose provider failures |
| Resource consumption | Periodic metrics | Cannot detect resource exhaustion |
| Event bus subscriber count | Lifecycle metrics | Cannot monitor bus health |
| Governance decision reasoning | GovernanceEvent | Cannot audit governance |
| Action parameter summary | ActionCreated event | Cannot reconstruct intent |
| System health snapshot | Periodic metrics | Cannot correlate failures with system state |

### Observability Layer Assessment

| Component | Lines | Integration | Assessment |
|-----------|------:|-------------|------------|
| Logger | 7 | Not wired | Single-line wrapper around Python logging |
| MetricsCollector | 60 | Not wired | Basic counters and timers, no export |
| TraceContext | 25 | Not wired | Plain data class, no propagation |

**The observability layer is a skeleton.** It defines the right abstractions (logging, metrics, tracing) but the implementations are minimal and none are integrated into the runtime kernel, event bus, or executor. There is no evidence that metrics are collected or traces are produced during normal operation.

This is the most significant architectural gap in v0.1.

---

## 12. Failure Isolation Findings

### Which Failures Are Isolated

| Failure Class | Isolation Boundary | Evidence |
|---------------|-------------------|----------|
| Provider execution failure | Executor wraps provider in try/except | Adversarial tests |
| Provider validation failure | Executor validates before governance | Adversarial tests |
| Subscriber failure | EventBus wraps each subscriber | Adversarial tests |
| Invalid state transition | StateManager rejects invalid transitions | Adversarial tests |
| Governance denial | Executor checks governance before execution | Adversarial tests |
| Concurrent action interference | Each action has independent state | Adversarial tests |

### Which Failures Still Propagate

| Failure Class | Propagation Path | Impact |
|---------------|-----------------|--------|
| EventBus stop | publish() raises RuntimeError | All subscribers fail |
| Kernel lifecycle error | initialize()/start() exceptions propagate to caller | Runtime cannot start |
| State manager memory exhaustion | _action_states grows unboundedly | Process OOM |
| Event loop starvation | Slow subscriber blocks all publish calls | System-wide latency |
| Unconfigured provider | RegistryError propagates to caller | Action fails |

### What Failure Boundaries Should Change

1. **State manager needs memory bounds.** The _action_states dict should have a maximum size or eviction policy.
2. **EventBus needs backpressure.** Slow subscribers should be detected and potentially dropped.
3. **Kernel lifecycle needs error recovery.** If initialize() partially succeeds and then fails, the kernel should clean up rather than leaving components in inconsistent states.
4. **Provider failures need richer error context.** The current ACTION_FAILED event contains only a string error. Stack traces, error categories, and retry information would be more useful.
5. **The observability layer needs its own failure isolation.** If a metric subscriber fails, it should not affect the event bus or other subscribers. This is already implemented but needs testing at scale.

---

## 13. Performance Findings

### Measured Performance vs. Original Targets

The v0.1 specification did not define explicit performance targets. The benchmarks establish baseline characteristics for the runtime substrate.

| Metric | Measured | Interpretation |
|--------|----------|----------------|
| Event Bus throughput | ~263K eps | 263,000 events per second in-process |
| Event Bus p50 latency | 4.4 us | Sub-5-microsecond delivery |
| Event Bus p95 latency | 4.6 us | Tight distribution |
| Event Bus p99 latency | 4.7 us | Minimal tail latency |
| Kernel startup p50 | 0.02 ms | 20 microseconds to start |
| Kernel shutdown p50 | 0.01 ms | 10 microseconds to stop |
| Action execution p50 | 0.02 ms | 20 microseconds per action |
| Action execution p99 | 0.05 ms | 50 microseconds at the 99th percentile |

### Bottlenecks

1. **Subscriber scaling.** Throughput degrades from 263K to 61K eps when subscriber count increases from 1 to 100. This is a linear degradation caused by sequential dispatch. For the v0.1 research workload (likely 1-5 subscribers), this is not a problem.

2. **Sequential dispatch.** The EventBus awaits each subscriber before calling the next. This means the slowest subscriber determines the minimum latency for each publish. This is the correct trade-off for v0.1 (simplicity and ordering guarantees over throughput).

3. **No batching.** Each event is dispatched individually. For high-throughput scenarios, batch dispatch could reduce per-event overhead.

4. **No caching.** The capability registry performs a dictionary lookup on every esolve() call. For v0.1 with 3 registered capabilities, this is negligible. For a system with thousands of capabilities, caching would help.

### Do NOT Propose Premature Optimization

The current performance is adequate for v0.1 research workloads. The identified bottlenecks are real but not urgent. Premature optimization would add complexity without measurable benefit at this stage.

The correct approach for v0.2 is to:

1. Add performance benchmarks as regression tests
2. Measure performance with realistic workloads
3. Optimize only when measurements show a problem

---

## 14. Developer Experience Findings

### Implementation Complexity

The runtime is simple. All core components are under 210 lines. The largest file is state/manager.py at 203 lines. The smallest is logger.py at 7 lines. A developer can read the entire runtime in under an hour.

The code follows consistent patterns:

- Dataclasses for models (frozen where immutability is needed)
- Async methods for runtime operations
- Type hints throughout
- Docstrings on public methods

### Testing Complexity

The test suite is well-structured:

- Unit tests are isolated (each test creates fresh components)
- Adversarial tests are organized by failure class (6 categories)
- Integration tests validate full pipeline wiring
- E2E tests validate the public API contract

The main testing challenge is the lack of dependency injection, which forces monkeypatching for unit tests that need to mock dependencies.

### Debugging Complexity

**High.** The observability layer is not wired into the runtime. This means:

- No structured logs during execution
- No metric dashboards
- No trace correlation across events
- No execution timing information

Debugging currently requires:

1. Reading the event stream (via captured events in tests)
2. Inspecting state transitions manually
3. Adding print statements or breakpoints

This is the most significant developer experience gap.

### API Ergonomics

The public API is clean:

`python
async with AURARuntime() as runtime:
    await runtime.initialize()
    await runtime.start()
    result = await runtime.execute(action)
    health = await runtime.health()
    await runtime.stop()
`

This is easy to understand and use. The async context manager pattern provides clean resource management.

### Repository Structure

The repository is well-organized:

`
src/aura/
  models/          # Data models
  runtime/         # Core runtime (kernel, event bus, state, governance, registry)
  execution/       # Executor and providers
  observability/   # Stubs
tests/
  unit/            # Component tests
  integration/     # Pipeline tests
  e2e/             # Lifecycle tests
benchmarks/        # Performance benchmarks
research/          # Experiments
docs/              # Documentation
`

This separation is clean and makes it easy to find components.

---

## 15. Technical Debt

The following technical debt is intentionally carried forward from v0.1:

| # | Debt Item | Severity | Impact |
|---|-----------|----------|--------|
| 1 | Observability stubs not wired into runtime | High | Cannot debug or monitor at scale |
| 2 | No persistence layer | High | Cannot recover from process failure |
| 3 | No timeout enforcement (ActionPolicy.timeout_ms ignored) | Medium | Hung actions are never detected |
| 4 | No retry logic (ActionPolicy.retry_count ignored) | Medium | Transient failures are not retried |
| 5 | Assert-based access guards (stripped under -O) | Low | Potential AttributeError in optimized mode |
| 6 | Unbounded state manager growth (_action_states dict) | High | Memory leak in long-running runtime |
| 7 | Hardcoded EventType subscription list in kernel | Medium | O/C violation, requires kernel edit for new events |
| 8 | No configuration injection (AuraConfig unused) | Medium | Runtime behavior not configurable |
| 9 | No concurrent lifecycle protection | Low | Only affects multi-threaded initialization |
| 10 | No v0.1.0 release tag created | Low | Release baseline not immutably recorded |

**Recommended priority for v0.2:** Items 1, 6, 8 (observability, memory bounds, configuration).

---

## 16. Architectural Risks

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| Memory leak from unbounded state growth | High | High (long-running runtime) | Add eviction policy or persistence |
| Observability gaps prevent debugging at scale | High | High (any non-trivial workload) | Wire observability into runtime |
| Sequential dispatch bottleneck | Medium | Low (v0.1 research workload) | Not urgent; measure before optimizing |
| Governance too simple for real policies | Medium | Low (v0.1 scope) | Architectural boundary exists; policy model can evolve |
| No concurrent lifecycle protection | Low | Low (single-process, asyncio) | Only affects multi-threaded use |
| Event bus single-process limitation | Low | Low (v0.1 is in-process) | Future versions may need distributed transport |
| No timeout/retry enforcement | Medium | Medium (provider hangs) | Add timeout support in v0.2 |
| Configuration not injectable | Medium | Medium (any customization needed) | Add DI or config injection in v0.2 |

---

## 17. Research Findings

The most important findings from implementing v0.1:

### 17.1 A Capability-Oriented Runtime Can Be Minimal

The entire runtime is approximately 1,086 lines. This is small enough for a single developer to understand completely. The architecture does not require complex abstractions to achieve capability independence.

**Implication:** Complexity should be added only when measurements demonstrate a need. The minimal design is a strength, not a weakness.

### 17.2 Event-Driven Coordination Is Achievable Without Infrastructure

The EventBus achieves 263K eps with 4.4us latency using only Python asyncio. No external message broker is needed for a single-process runtime.

**Implication:** The architectural decision to use in-process events is validated. External infrastructure is a scaling concern, not an architectural requirement.

### 17.3 Governance-Before-Execution Is Structurally Enforceable

The execution pipeline places governance before provider execution. This is not a convention -- it is a structural property of the code. A denied action cannot reach a provider without bypassing the executor.

**Implication:** Future cognitive systems can trust that governance is enforced, regardless of how they generate actions.

### 17.4 Simple Failure Isolation Is Achievable

The adversarial test suite demonstrates that provider failures, subscriber failures, invalid transitions, and governance denials are all isolated. The runtime remains operational after failures.

**Implication:** The fault-containment boundaries are sound for the tested failure classes. Production deployment would require testing against additional failure classes (process termination, resource exhaustion, adversarial providers).

### 17.5 Observability Is the Primary Gap

The observability layer is 92 lines, none wired into the runtime. Without structured logging, metric export, and trace propagation, the runtime cannot be debugged, monitored, or reasoned about at scale.

**Implication:** This should be the first priority for v0.2. The architectural boundary for observability is in place (EventBus subscriber isolation); the implementation just needs to be completed.

---

## 18. Unanswered Questions

The following questions emerged from v0.1 and remain unanswered:

### Runtime State

How should runtime state become persistent and recoverable without tightly coupling persistence to execution? The current in-memory state model is clean but volatile.

### Event History

Can the Event Bus evolve into a durable event history without turning the runtime into a distributed infrastructure project prematurely? The current in-process model is fast but ephemeral.

### Context

How should runtime state, session state, memory, and environmental information be represented as a unified context model? The current model has no concept of "context" beyond action parameters.

### Scheduling

How should AURA allocate computation dynamically according to task complexity, latency requirements, resource availability, confidence, and energy constraints? The current model executes all actions equally.

### Governance

How should governance evolve from a simple allow/deny gate into a policy-aware decision system? The architectural boundary exists; the policy model needs to become richer.

### Cognition

How should reasoning, planning, memory, learning, and reflection interact with the Runtime Core without contaminating the kernel with cognitive-specific logic? This is the fundamental architectural question for AURA.

---

## 19. Candidate v0.2 Research Directions

Ranked by five criteria: architectural importance, dependency on Runtime Core, research value, implementation risk, and ability to produce measurable evidence.

| Rank | Direction | Architectural Importance | Dependency | Research Value | Risk | Measurable Evidence |
|------|-----------|------------------------|------------|----------------|------|---------------------|
| 1 | Structured Observability | High | Low | High | Low | Yes -- metric dashboards, trace views |
| 2 | State Persistence | High | High | High | Medium | Yes -- recovery success rate |
| 3 | Configuration Injection | Medium | Low | Medium | Low | Yes -- configurable runtime behavior |
| 4 | Timeout/Retry Enforcement | Medium | Low | Medium | Low | Yes -- hung action detection rate |
| 5 | Memory Bounds | High | Low | Medium | Low | Yes -- memory usage under load |
| 6 | Richer Governance | Medium | Medium | High | Medium | Yes -- policy evaluation metrics |
| 7 | Distributed Event Bus | Medium | High | High | High | Yes -- cross-process event delivery |
| 8 | Context Model | High | High | High | High | Yes -- context reconstruction accuracy |

### Recommended Direction

**Structured Observability** is the recommended first direction for v0.2 because:

1. It has high architectural importance (observability is the primary gap)
2. It has low dependency on Runtime Core (can be added without modifying kernel logic)
3. It has high research value (enables all future experiments to be measured)
4. It has low implementation risk (incremental addition, not architectural change)
5. It produces immediate measurable evidence (metric dashboards, trace views)

---

## 20. Recommended Next Step

**No implementation.** This retrospective is a research artifact.

The recommended next step is a **research question**, not a feature:

> How should AURA's observability layer be structured so that runtime behavior can be reconstructed, measured, and monitored without modifying the runtime kernel?

This question should be answered before any v0.2 implementation begins.

---

**Adaptive Intelligence Research Lab**

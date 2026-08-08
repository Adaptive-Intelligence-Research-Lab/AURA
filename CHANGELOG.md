# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - Unreleased

### Planned
- Session Manager
- Context Engine
- Agent Scheduler
- Resource Manager
- Extended Governance Engine

## [0.1.0] - 2026-08-08

### Added
- **EventBus** — Async publish/subscribe event distribution with error isolation
- **CapabilityRegistry** — Dynamic capability registration, resolution, and lookup
- **StateManager** — Event-driven lifecycle tracking with validated state transitions
- **GovernanceGate** — Allow/deny policy engine for capability access control
- **CapabilityExecutor** — Orchestrates validate → governance → execute lifecycle
- **AURARuntime** — Central kernel coordinating all subsystems (initialize/start/execute/health/stop)
- **3 Capability Providers** — `core.echo`, `core.system_info`, `core.sleep`
- **7 Data Models** — actions, events, capabilities, execution, state, config, errors
- **Observability Stubs** — MetricsCollector, TraceContext, Logger
- **153 Tests** — Unit (models, runtime, execution, observability, adversarial), integration, E2E
- **Performance Benchmarks** — 265k events/sec, 4.4μs p50 latency, 0.02ms action execution
- **Research Experiments** — Capability independence, event reconstruction, failure isolation (all SUPPORTED)
- **GitHub Actions CI** — Lint (ruff), type check (mypy), test (pytest) on push/PR
- **Implementation Documentation** — AURA-IMPL-001 results and compliance review

### Changed
- Renamed `RuntimeKernel` to `AURARuntime` with spec-aligned API
- Execution lifecycle fixed to spec order: validate → ACTION_VALIDATED → governance → ACTION_STARTED → execute → COMPLETED/FAILED
- State transitions now include VALIDATED → QUEUED → RUNNING (not bypassed)
- `correlation_id` propagated through all events for traceability

### Fixed
- Governance denial now publishes ACTION_FAILED event (observable failure)
- `datetime.UTC` used consistently (Python 3.11+)

## [0.0.1] - 2026-08-02

### Added
- Initial repository setup
- Documentation framework
- Architecture specifications (AURA-000 through AURA-017)
- Branching strategy and contribution guidelines

[unreleased]: https://github.com/Adaptive-Intelligence-Research-Lab/AURA/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Adaptive-Intelligence-Research-Lab/AURA/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Adaptive-Intelligence-Research-Lab/AURA/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/Adaptive-Intelligence-Research-Lab/AURA/releases/tag/v0.0.1

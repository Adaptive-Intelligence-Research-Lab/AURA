# AURA - Adaptive Unified Reasoning Agent

> The flagship project of the **Adaptive Intelligence Research Lab (AIR Lab)**

AURA is a research-grade, offline-first adaptive intelligence platform. The long-term goal is a personal AI operating environment capable of reasoning, remembering, planning, learning, reflecting, and autonomously executing tasks across multiple devices.

**Current Status:** v0.1.0 — Runtime Core (Event-driven capability execution framework)

---

## Quick Start

```bash
# Clone
git clone https://github.com/Adaptive-Intelligence-Research-Lab/AURA.git
cd AURA

# Create virtual environment (requires Python 3.11+)
python -m venv .venv311
.venv311\Scripts\activate  # Windows
# source .venv311/bin/activate  # Linux/Mac

# Install
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check src/ tests/

# Type check
mypy src/aura/ --ignore-missing-imports
```

---

## What's Implemented (v0.1.0)

The Runtime Core provides an event-driven capability execution framework:

| Component | Description |
|-----------|-------------|
| **EventBus** | Async publish/subscribe event distribution with error isolation |
| **CapabilityRegistry** | Dynamic capability registration, resolution, and lookup |
| **StateManager** | Event-driven lifecycle tracking with validated state transitions |
| **GovernanceGate** | Allow/deny policy engine for capability access control |
| **CapabilityExecutor** | Orchestrates validate → governance → execute lifecycle |
| **AURARuntime** | Central kernel coordinating all subsystems |
| **3 Providers** | `core.echo`, `core.system_info`, `core.sleep` |

### Validation

- **153 tests** — all passing (unit, integration, E2E)
- **ruff** — all checks passed
- **mypy** — 0 errors (30 source files)
- **3 experiments** — capability independence, event reconstruction, failure isolation (all SUPPORTED)
- **Benchmarks** — 265k events/sec, 4.4μs p50 latency, 0.02ms action execution

---

## Repository Structure

```
AURA/
├── src/aura/                  # Source code
│   ├── models/                #   Data models (actions, events, state, config, errors)
│   ├── runtime/               #   Runtime kernel, event bus, state manager, governance
│   │   ├── event_bus/         #     Async event bus
│   │   ├── governance/        #     Governance gate
│   │   ├── registry/          #     Capability registry
│   │   └── state/             #     State manager
│   ├── execution/             #   Executor and capability providers
│   │   └── providers/         #     echo, system_info, sleep
│   └── observability/         #   Metrics, tracing, logger (stubs)
├── tests/                     # Test suite
│   ├── unit/                  #   Unit tests (models, runtime, execution, observability)
│   ├── integration/           #   Integration tests
│   └── e2e/                   #   End-to-end tests
├── benchmarks/                # Performance benchmarks
├── research/experiments/      # Research hypothesis experiments
├── docs/                      # Documentation
│   ├── architecture/          #   System architecture
│   ├── specifications/        #   Spec documents (AURA-SPEC-001 through 010)
│   ├── implementation/        #   Implementation results and compliance
│   └── adr/                   #   Architecture Decision Records
├── examples/                  # Example scripts
├── adr/                       # ADR index
├── pyproject.toml             # Project configuration
├── CONTRIBUTING.md            # Contributing guidelines
├── ROADMAP.md                 # Project milestones
└── CHANGELOG.md               # Release history
```

---

## Architecture Overview

The platform is designed in layers:

1. **Interaction Layer** — Voice, Text, Vision, API
2. **Runtime Kernel** — Event Bus, State Manager, Governance Engine, Capability Registry
3. **Cognitive Services** — Reasoning, Memory, Planning, Learning, Reflection
4. **Execution Layer** — Desktop, Android, Browser, Terminal Agents
5. **Storage Layer** — Memory Store, Cache, Knowledge Graph, Vector Store

Currently implemented: **Runtime Kernel** (layer 2, core components).

For detailed architecture documentation, see [docs/architecture/](docs/architecture/).

---

## Documentation

| Document | Description |
|----------|-------------|
| [Contributing Guidelines](CONTRIBUTING.md) | Branching strategy, commit conventions, PR workflow |
| [Architecture](docs/architecture/) | System architecture specifications |
| [Specifications](docs/specifications/) | AURA-SPEC-001 through 010 |
| [Implementation](docs/implementation/) | v0.1.0 results and compliance review |
| [Changelog](CHANGELOG.md) | Release history |
| [Roadmap](ROADMAP.md) | Project milestones |

---

## Development

- **Python 3.11+** required
- **Commit format:** [Conventional Commits](https://www.conventionalcommits.org/)
  ```
  feat(runtime): add event bus
  fix(executor): resolve governance bypass
  docs(spec): update AURA-SPEC-003
  test(models): add action model tests
  ```
- **Branches:** Feature branches → `develop`, Documentation → `main`
- See [CONTRIBUTING.md](CONTRIBUTING.md) for full details

---

## License

AIR Lab Research License

---

**Adaptive Intelligence Research Lab**

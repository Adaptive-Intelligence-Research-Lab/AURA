# Contributing to AURA

## Branching Strategy

AURA uses a **two-branch integration model**: `develop` is the active integration branch, `main` is the stable documentation branch.

### Branch Roles

| Branch | Purpose | Merges From | Lifetime |
|--------|---------|-------------|----------|
| `main` | Stable documentation and specifications | `docs/*` branches | Permanent |
| `develop` | Active integration branch | `feat/*`, `fix/*`, `refactor/*` | Permanent |
| `feat/*` | New implementation | — | Short, merged into `develop` |
| `docs/*` | Documentation updates | — | Short, merged into `main` |
| `fix/*` | Bug fixes | — | Short, merged into `develop` |
| `refactor/*` | Internal improvements | — | Short, merged into `develop` |
| `research/*` | Research and exploration | — | Variable, optional merge |
| `experiment/*` | Proofs of concept | — | Short–medium, optional merge |

### Branch Diagram

```
main ─────────●──────────────────●──────────────
              │                  ↑
              │            docs/runtime-core
              │
develop ──●───●───●───●───●───●───●───●────────
          │       ↑   │       ↑       ↑
          │       │   │       │       │
     feat/event-bus  feat/state-mgr  feat/aura-v0.1
```

### Branch Naming Conventions

```
feat/event-bus
feat/capability-registry
feat/state-manager
feat/aura-v0.1-spec-alignment
docs/runtime-core
docs/spec-003
fix/executor-governance
refactor/kernel-lifecycle
research/adaptive-memory
experiment/context-graph
```

### Pull Request Workflow

**Feature branches → `develop`:**

```
Issue / Task
    │
    ▼
Create feat/branch from develop
    │
    ▼
Develop + test locally
    │
    ▼
Push to origin
    │
    ▼
Open Pull Request → develop
    │
    ▼
CI passes (pytest, ruff, mypy)
    │
    ▼
Merge (squash or merge commit)
```

**Documentation branches → `main`:**

```
docs/branch from main
    │
    ▼
Write documentation
    │
    ▼
Open Pull Request → main
    │
    ▼
Merge
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

feat(runtime): add event dispatcher
feat(memory): implement episodic memory interface
docs(spec): update AURA-SPEC-003
fix(executor): resolve governance bypass
test(models): add action model tests
refactor(kernel): simplify lifecycle management
chore(ci): add GitHub Actions workflow
```

**Types:** `feat`, `docs`, `fix`, `test`, `refactor`, `chore`, `perf`, `ci`, `build`, `research`, `experiment`

### Scopes

Common scopes for this project:

- `runtime` — Runtime kernel, event bus, state manager
- `execution` — Executor and capability providers
- `models` — Data models (actions, events, state, config)
- `governance` — Governance gate
- `observability` — Metrics, tracing, logger
- `spec` — Specification documents
- `ci` — CI/CD configuration

### Branch Protection Rules (GitHub)

**On `develop`:**

- Require Pull Requests
- Require passing CI checks (pytest, ruff, mypy)
- Allow self-approval (solo contributor)

**On `main`:**

- Prevent direct pushes
- Require Pull Requests

### Release Strategy

Merge `develop` into `main` and tag stable milestones:

```
v0.1.0   Runtime Core (Event Bus, State Manager, Governance, Executor)
v0.2.0   Runtime Kernel (Session, Context, Scheduler, Resources)
v0.3.0   Memory + Reasoning
v0.4.0   Planning
v0.5.0   Desktop Automation
v0.6.0   Android Automation
v1.0.0   First Complete Offline Agent
```

### Development Setup

```bash
# Clone
git clone https://github.com/Adaptive-Intelligence-Research-Lab/AURA.git
cd AURA

# Create virtual environment (Python 3.11+)
python -m venv .venv311
.venv311\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check src/ tests/

# Type check
mypy src/aura/ --ignore-missing-imports
```

---

**Adaptive Intelligence Research Lab**

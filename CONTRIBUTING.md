# Contributing to AURA

## Branching Strategy

AURA uses a branching model inspired by **GitHub Flow + Trunk-Based Development + Research Branches**.

### Branch Categories

| Branch Type | Lifetime | Merge Required | Purpose |
|---|---|---|---|
| `main` | Permanent | N/A | Stable, releasable state |
| `feature/*` | Short | Yes | New implementation |
| `docs/*` | Short | Yes | Documentation updates |
| `research/*` | Variable | Optional | Research and exploration |
| `experiment/*` | Short–Medium | Optional | Proofs of concept |
| `prototype/*` | Medium | Usually | Larger integrated prototypes |
| `refactor/*` | Short | Yes | Internal improvements |
| `bugfix/*` | Short | Yes | Standard bug fixes |
| `hotfix/*` | Very Short | Yes | Critical production fixes |
| `release/*` | Short | Yes | Final release preparation |

### Branch Naming Conventions

```
docs/reference-architecture
docs/runtime-kernel
docs/memory-system
docs/planning-system

research/adaptive-memory
research/cognitive-routing
research/runtime-learning
research/meta-reasoning

experiment/qwen-routing
experiment/graph-memory
experiment/hybrid-planning
experiment/local-rag

feature/voice-engine
feature/android-controller
feature/desktop-controller
feature/plugin-sdk
feature/browser-agent

refactor/context-cache
refactor/runtime-api
refactor/event-fabric

bugfix/scheduler-timeout
hotfix/memory-leak
release/v0.2.0
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/) from day one:

```
<type>(<scope>): <description>

feat(runtime): add event dispatcher
feat(memory): implement episodic memory interface
docs(architecture): complete planning system
research(reflection): define evaluation framework
experiment(graph): prototype context graph
refactor(kernel): simplify lifecycle management
fix(scheduler): resolve deadlock issue
test(runtime): add event bus integration tests
chore(repo): update gitignore
```

**Types:** `feat`, `docs`, `research`, `experiment`, `refactor`, `fix`, `test`, `chore`, `perf`, `ci`, `build`

### Phase 1 — Documentation & Architecture (Current)

```
main
│
├── docs/reference-architecture
├── docs/runtime
├── docs/cognition
├── docs/specifications
└── research/adaptive-control-plane
```

Every branch merges into `main` after review. No permanent develop branch.

### Phase 2 — Implementation

```
main
│
├── feature/runtime-kernel
├── feature/event-bus
├── feature/session-manager
├── feature/context-engine
├── feature/reasoning-system
├── feature/memory-system
├── feature/planning-system
├── feature/android-agent
└── feature/desktop-agent
```

Each feature is isolated and merged through a Pull Request.

### Pull Request Workflow

```
Issue
  │
  ▼
Create Branch
  │
  ▼
Develop
  │
  ▼
Self Review
  │
  ▼
Open Pull Request
  │
  ▼
Architecture Review
  │
  ▼
Merge to main
```

Even as a solo contributor, use Pull Requests. They create a searchable review history.

### Branch Protection Rules (GitHub)

Configure on `main`:

- Prevent direct pushes
- Require Pull Requests
- Require passing CI checks
- Require at least one approval (self-approve when solo)
- Keep a linear commit history

### Release Strategy

Tag stable milestones:

```
v0.1.0   Documentation complete
v0.2.0   Runtime kernel prototype
v0.3.0   Memory + reasoning
v0.4.0   Planning
v0.5.0   Desktop automation
v0.6.0   Android automation
v1.0.0   First complete offline agent
```

### Branch Lifecycle

```
main
 │
 ├── feature/runtime-kernel
 │          │
 │          └──────────────┐
 │                         ▼
 │                      Pull Request
 │                         │
 │                         ▼
 ├────────────────────────►main
 │
 ├── research/adaptive-memory
 │
 ├── experiment/context-graph
 │
 └── docs/reference-architecture
```

Research and experiment branches can remain open for months or be archived if the ideas don't pan out.

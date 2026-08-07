# AURA-SPEC-002: Action Object

**Project:** AURA (Adaptive Unified Reasoning Agent)

**Specification ID:** AURA-SPEC-002

**Version:** 1.0.0-draft

**Status:** Draft

**Author:** Adaptive Intelligence Research Lab (AIR Lab)

**Category:** Runtime Specification

**Last Updated:** 2026-08-04

---

# 1. Purpose

This specification defines the Action Object, the canonical execution message exchanged throughout the Adaptive Intelligence Runtime (AIR Runtime).

The Action Object represents a single executable unit produced by cognition and consumed by the Action Layer.

Every executable operation SHALL be represented as an Action Object.

---

# 2. Scope

This specification applies to:

- Planning System
- Workflow Runtime Engine
- Action Execution Framework
- Capability Orchestration Engine
- Execution Adapters
- Execution Supervision Engine
- Governance Engine
- Plugin Execution Adapter

---

# 3. Design Goals

The Action Object shall be:

- Immutable after creation (except runtime state)
- Platform independent
- Capability driven
- Observable
- Serializable
- Versioned
- Secure
- Extensible

---

# 4. Definition

An Action Object is a structured runtime message that expresses an executable intent.

It defines:

- Why the action exists
- Which capability is requested
- How execution should occur
- How runtime tracks execution

It never contains platform-specific implementation details.

---

# 5. Action Object Architecture

Every Action Object consists of four logical layers.

```text
Action Object

├── Intent Layer

├── Capability Layer

├── Execution Layer

└── Runtime Layer
```

---

# 6. Intent Layer

Describes why the action exists.

Fields include:

| Field | Description |
|--------|-------------|
| Action ID | Globally unique identifier |
| Goal ID | Parent goal |
| Workflow ID | Parent workflow |
| Parent Action | Parent action identifier |
| Description | Human-readable intent |
| Priority | Execution priority |

The Intent Layer provides semantic context.

---

# 7. Capability Layer

References the capability specification.

Fields include:

| Field | Description |
|--------|-------------|
| Capability ID | Reference to AURA-SPEC-001 |
| Capability Version | Semantic version |
| Parameters | Capability inputs |
| Expected Outputs | Declared outputs |

The Capability Layer contains no implementation logic.

---

# 8. Execution Layer

Defines execution behavior.

Fields include:

| Field | Description |
|--------|-------------|
| Execution Strategy | Sequential, Parallel, Conditional |
| Timeout | Maximum execution duration |
| Retry Policy | Retry configuration |
| Scheduling | Immediate, Delayed, Event-driven |
| Dependencies | Action dependencies |
| Resource Profile | Resource requirements |
| Security Context | Required permissions |

The Execution Layer influences orchestration.

---

# 9. Runtime Layer

Maintains runtime execution metadata.

Fields include:

| Field | Description |
|--------|-------------|
| State | Current lifecycle state |
| Created Timestamp | Creation time |
| Updated Timestamp | Last modification |
| Assigned Adapter | Selected execution adapter |
| Execution Graph ID | Owning graph |
| Session ID | Runtime session |
| Correlation ID | Distributed tracing |
| Telemetry ID | Monitoring reference |

The Runtime Layer is the only mutable portion of the Action Object.

---

# 10. Lifecycle

Every Action Object follows the lifecycle below.

```text
Created

↓

Validated

↓

Authorized

↓

Queued

↓

Dispatched

↓

Running

↓

Completed

↓

Failed

↓

Cancelled

↓

Archived
```

Lifecycle transitions are supervised by the Execution Supervision Engine.

---

# 11. Validation Rules

A valid Action Object SHALL:

- Reference an existing capability
- Contain a valid Action ID
- Define execution parameters
- Include runtime metadata
- Declare security context
- Be serializable
- Pass governance validation

Invalid Action Objects SHALL NOT enter execution.

---

# 12. Execution Semantics

The Action Object expresses intent only.

It never specifies:

- Which adapter executes it
- Which operating system executes it
- Which API executes it
- Which plugin executes it

These decisions belong to the Capability Orchestration Engine.

---

# 13. Security

The Action Object SHALL declare:

- Required permissions
- Session context
- Security classification
- Governance policy references

Execution without authorization is prohibited.

---

# 14. Error Conditions

Possible errors include:

- InvalidAction
- MissingCapability
- InvalidParameters
- UnauthorizedAction
- ValidationFailed
- UnsupportedVersion
- ExecutionRejected

Errors SHALL comply with the Runtime Error Model.

---

# 15. Reference Example

```yaml
action_id: action-6f3b21

goal_id: goal-20260804-001

workflow_id: workflow-daily-report

description: Launch Visual Studio Code

capability:
  id: capability.desktop.launch_application
  version: 1.0.0
  parameters:
    application: "Visual Studio Code"

execution:
  strategy: sequential
  timeout: 30s
  retry: 2

runtime:
  state: queued
  session: session-a91c
```

---

# 16. Relationship to Other Specifications

The Action Object depends on:

- AURA-SPEC-001 Capability Model

The Action Object is consumed by:

- Capability Orchestration Engine
- Workflow Runtime Engine
- Execution Supervision Engine
- Execution Adapters

---

# 17. Future Extensions

Future versions may support:

- Probabilistic execution metadata
- Confidence scores
- Cost estimation
- Multi-capability actions
- Adaptive execution hints
- Distributed execution metadata
- AI-generated execution annotations

---

# 18. Conclusion

The Action Object is the canonical execution message of the Adaptive Intelligence Runtime. It provides a platform-independent representation of executable intent, separating semantics, capability, execution policy, and runtime metadata. This separation enables adaptive orchestration, secure execution, observability, and long-term extensibility across heterogeneous execution environments.
# WorkStation Documentation

Index for the `docs/` tree. WorkStation hosts the **canonical platform
architecture docs** that other repos reference. The `architecture/` directory
is now subgrouped by concern: `system/`, `routing/`, `adapters/`, `contracts/`,
`execution/`, `policy/`.

## Architecture (canonical platform docs)

These are the source of truth for cross-repo system design. Other repos link
into this directory rather than duplicate.

### System

- [architecture/system/system_overview.md](architecture/system/system_overview.md) —
  Full platform design and component roles.
- [architecture/system/ownership.md](architecture/system/ownership.md) —
  Repo-level ownership model.
- [architecture/system/repo_responsibility_matrix.md](architecture/system/repo_responsibility_matrix.md) —
  Tabular ownership matrix.
- [architecture/system/glossary.md](architecture/system/glossary.md) —
  Cross-repo terminology.
- [architecture/adr/](architecture/adr/) — Architecture decision records.

### Routing

- [architecture/routing/operations-center-routing.md](architecture/routing/operations-center-routing.md) ·
  [examples](architecture/routing/operations-center-routing-examples.md)
- [architecture/routing/routing-fallback-escalation.md](architecture/routing/routing-fallback-escalation.md) ·
  [examples](architecture/routing/routing-fallback-escalation-examples.md)
- [architecture/routing/routing-tuning.md](architecture/routing/routing-tuning.md) ·
  [examples](architecture/routing/routing-tuning-examples.md)

### Adapters

- [architecture/adapters/kodo-adapter.md](architecture/adapters/kodo-adapter.md) ·
  [examples](architecture/adapters/kodo-adapter-examples.md)
- [architecture/adapters/archon-adapter.md](architecture/adapters/archon-adapter.md) ·
  [examples](architecture/adapters/archon-adapter-examples.md)
- [architecture/adapters/openclaw-backend-adapter.md](architecture/adapters/openclaw-backend-adapter.md) ·
  [examples](architecture/adapters/openclaw-backend-adapter-examples.md)
- [architecture/adapters/openclaw-outer-shell.md](architecture/adapters/openclaw-outer-shell.md) ·
  [examples](architecture/adapters/openclaw-outer-shell-examples.md)
- [architecture/adapters/local-lane.md](architecture/adapters/local-lane.md)

### Contracts

- [architecture/contracts/contracts.md](architecture/contracts/contracts.md) ·
  [examples](architecture/contracts/contracts-examples.md)
- [architecture/contracts/upstream-patch-evaluation.md](architecture/contracts/upstream-patch-evaluation.md) ·
  [examples](architecture/contracts/upstream-patch-evaluation-examples.md)

### Execution

- [architecture/execution/execution-observability.md](architecture/execution/execution-observability.md) ·
  [examples](architecture/execution/execution-observability-examples.md)

### Policy

- [architecture/policy/policy-guardrails.md](architecture/policy/policy-guardrails.md) ·
  [examples](architecture/policy/policy-guardrails-examples.md)

### High-level overview

- [architecture.md](architecture.md) — Top-level architecture entry-point doc
  (kept for inbound links; new material goes under `architecture/`).

## Operations

- [operations/archon-setup.md](operations/archon-setup.md) — Archon stack
  bring-up and validation.
- [operations/local-lane-setup.md](operations/local-lane-setup.md) — Local lane
  (aider_local) tiny-model deployment.
- [environments.md](environments.md) — Environment topology.
- [health-model.md](health-model.md) — Health-check policy across services.
- [local_aider_lane.md](local_aider_lane.md) — Operator notes for the
  `aider_local` lane.

## History

- [history/](history/) — Final-phase checklists, legacy remediation summaries,
  the historical 9router removal notes, and other one-shot historical material.

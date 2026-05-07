# WorkStation Documentation

Index for the `docs/` tree. WorkStation hosts the **canonical platform
architecture docs** that other repos reference (kodo/archon/openclaw adapters,
contracts, routing, policy guardrails, ownership model). It also holds
WorkStation-local operations material.

## Architecture (canonical platform docs)

These are the source of truth for cross-repo system design. Other repos link
into this directory rather than duplicate.

### System

- [architecture/system_overview.md](architecture/system_overview.md) — Full
  platform design and component roles.
- [architecture/ownership.md](architecture/ownership.md) — Repo-level ownership
  model (who owns what, where each concern lives).
- [architecture/repo_responsibility_matrix.md](architecture/repo_responsibility_matrix.md) —
  Tabular ownership matrix.
- [architecture/glossary.md](architecture/glossary.md) — Cross-repo terminology.
- [architecture/adr/](architecture/adr/) — Architecture decision records.

### Contracts

- [architecture/contracts.md](architecture/contracts.md)
- [architecture/contracts-examples.md](architecture/contracts-examples.md)

### Routing & Policy

- [architecture/operations-center-routing.md](architecture/operations-center-routing.md)
- [architecture/operations-center-routing-examples.md](architecture/operations-center-routing-examples.md)
- [architecture/routing-fallback-escalation.md](architecture/routing-fallback-escalation.md)
- [architecture/routing-fallback-escalation-examples.md](architecture/routing-fallback-escalation-examples.md)
- [architecture/routing-tuning.md](architecture/routing-tuning.md)
- [architecture/routing-tuning-examples.md](architecture/routing-tuning-examples.md)
- [architecture/policy-guardrails.md](architecture/policy-guardrails.md)
- [architecture/policy-guardrails-examples.md](architecture/policy-guardrails-examples.md)

### Backend Adapters

- [architecture/kodo-adapter.md](architecture/kodo-adapter.md) ·
  [examples](architecture/kodo-adapter-examples.md)
- [architecture/archon-adapter.md](architecture/archon-adapter.md) ·
  [examples](architecture/archon-adapter-examples.md)
- [architecture/openclaw-backend-adapter.md](architecture/openclaw-backend-adapter.md) ·
  [examples](architecture/openclaw-backend-adapter-examples.md)
- [architecture/openclaw-outer-shell.md](architecture/openclaw-outer-shell.md) ·
  [examples](architecture/openclaw-outer-shell-examples.md)
- [architecture/local-lane.md](architecture/local-lane.md)

### Cross-Cutting

- [architecture/execution-observability.md](architecture/execution-observability.md) ·
  [examples](architecture/execution-observability-examples.md)
- [architecture/upstream-patch-evaluation.md](architecture/upstream-patch-evaluation.md) ·
  [examples](architecture/upstream-patch-evaluation-examples.md)

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


# Objectives

_Durable work inventory — broader than the active mission, narrower than a full backlog._
_Update after each meaningful chunk of progress. Keep it short and actionable._

## In Progress

(none)

## Up Next

- [ ] **Archon real workflow integration (OC-side)** — the compose profile is in place and the OC adapter does a health probe, but actual workflow dispatch is not wired. Archon's API is conversation-driven and async (`POST /api/workflows/{name}/run` with `{conversationId, message}` returns 202; results come via `GET /api/workflows/runs/{runId}` polling or `GET /api/stream/{conversationId}` SSE). Needs a design doc deciding: how does `ExecutionRequest.goal_text` map to a conversation message? Per-task vs reused conversationId? OC's policy semantics for `approval_required`? Owner: OperationsCenter, with this compose profile as the deployment dependency.

## Done

- [x] **Archon compose profile** — `compose/profiles/archon.yml` builds from sibling `Velascat/Archon` clone, exposes `PORT_ARCHON` (default 3000), persists state under `runtime/archon`, health-checks `GET /api/health`. Docs in `docs/operations/archon-setup.md`. (2026-05-06)

---

_Completed items can be archived to mission-log.md. This is not the primary task tracker — keep it focused._

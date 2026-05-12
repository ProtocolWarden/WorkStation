# Archon Real Workflow Integration — Design

**Status:** Shipped 2026-05-07 ([OC #85](https://github.com/ProtocolWarden/OperationsCenter/pull/85), [ER #6](https://github.com/ProtocolWarden/ExecutorRuntime/pull/6)). Live-validated against a real Archon container the same day.
**Owner:** OperationsCenter
**Companion:** [archon-adapter.md](archon-adapter.md) (architectural overview, abstract adapter pattern)

**Approved 2026-05-07.** D1/D2/D3 confirmed by operator; all three open questions resolved inline below. Implementation landed as a single OC PR + a coordinated ExecutorRuntime PR; live-validation against a real Archon container surfaced two corrections to the table of bundled workflow names and one note on the empty `/api/workflows` listing — see *"Real-API findings"* near the bottom.

---

## What this doc decides

The current `HttpArchonAdapter.run()` returns a `failure` outcome with the
literal text *"workflow dispatch is not yet implemented"*. This doc closes
that gap by specifying:

1. How an OC `ExecutionRequest` becomes an Archon workflow run.
2. How OC tracks and polls that run to completion.
3. How Archon's lifecycle states map back to OC's `ExecutionResult`.
4. How the new `AsyncHttpRunner` (already shipped in ExecutorRuntime) is
   wired in.

The doc is the gate referenced by:
- OperationsCenter `.console/log.md` backlog: *"Archon real workflow integration"*
- The deferred *"Switch to AsyncHttpRunner"* archon adoption (also in the OC backlog).

---

## What we're integrating with

Archon is a TypeScript/bun monorepo (deployed by PlatformDeployment via
`compose/profiles/archon.yml`, default `http://localhost:3000`). Its
workflow surface is conversation-scoped and dispatches asynchronously.

### Endpoints we use

| Verb | Path | Purpose |
|---|---|---|
| `POST` | `/api/conversations` | Create a conversation. Body: `{codebaseId?, message?}`. Response: `{conversationId, id, dispatched?}`. Body is `.strict()` — unknown fields rejected. |
| `POST` | `/api/workflows/{name}/run` | Run a named workflow inside a conversation. Body: `{conversationId, message}`. Response: `{accepted: bool, status: string}` (DispatchResponse). **Fire-and-forget** — does not return run_id directly. |
| `GET` | `/api/workflows/runs/by-worker/{platformId}` | Resolve a conversation's worker `platformId` to a `runId`. Used after kickoff to obtain the run handle. |
| `GET` | `/api/workflows/runs/{runId}` | Run detail. Response: `{run: {…, status, metadata, …}, events: […]}`. **Source of truth for completion.** |
| `POST` | `/api/workflows/runs/{runId}/cancel` | Cancel a still-running workflow (timeout / abort). |
| `POST` | `/api/workflows/runs/{runId}/approve` | Approve a paused (approval-gate) run. v2; not used in v1. |
| `POST` | `/api/workflows/runs/{runId}/abandon` | Mark a paused/blocked run as abandoned. |

### Run statuses (Archon-side)

`pending` → `running` → terminal: `completed` | `failed` | `cancelled` | `paused`.

`paused` is *not* a failure — it indicates the workflow has hit an
approval-gate node and is waiting for human input (or `/approve` /
`/reject`). v1 maps it to `partial` outcome and surfaces it to the
operator without auto-approving.

### Workflow names

Workflows are YAML files under `.archon/workflows/` (recursive) plus
bundled defaults. Each declares `name`, `description`, optional
`provider` (`claude`/`codex`), optional `model`. OC selects the
workflow name based on `ArchonWorkflowConfig.workflow_type`:

| OC `workflow_type` | Archon workflow name (default) |
|---|---|
| `goal` | `archon-assist` |
| `fix_pr` | `archon-fix-github-issue` |
| `test` | `archon-test-loop-dag` |
| `improve` | `archon-refactor-safely` |

These are real names that ship as bundled defaults in
[ProtocolWarden/Archon][Archon] (`packages/workflows/src/defaults/`).
Operators override via `backends.archon.workflow_names: dict[str, str]`
in `config/operations_center.local.yaml` when shipping custom YAML
workflows. Missing-workflow at dispatch time → `outcome="failure"`
with `"unknown archon workflow: <type>"`.

> **Earlier draft note (kept for archival):** the original mapping
> proposed names like `archon-goal-default` / `archon-fix-github-issue-dag` /
> `archon-test-default` / `archon-improve-default`. None of those exist
> in Archon's bundled defaults. Live validation 2026-05-07 caught the
> divergence; the table above is the corrected mapping.

[Archon]: https://github.com/ProtocolWarden/Archon

---

## Decisions

### D1 — `goal_text` maps directly to the workflow message body ✅ confirmed

**Decision:** `ExecutionRequest.goal_text` becomes the `message` field of
`POST /api/workflows/{name}/run` verbatim. No prefix, no structured
header. **Strict** — `task_branch` and other OC-side context do **not**
get framed into the prompt either (see resolved open question 2 below).
If a workflow needs branch awareness, that's an Archon-side feature
request, not an OC frame.

**Rationale:**
- Archon workflows themselves know how to interpret task shape — the
  workflow YAML's `description`, `steps`, and command sequence encode
  the structure. OC doesn't need to pre-frame the prompt.
- Keeps OC out of the prompt-engineering business. If a workflow needs
  more context, it's the workflow author's job to add it (e.g. via a
  `archon-collect-context` step), not OC's.
- `goal_text` is already operator-authored; double-framing would be
  noise.

**Not chosen — structured prefix:** *"Repo: {repo_key}\nBranch: {task_branch}\n\n{goal_text}"*.
OC has the data, but pushing it into the prompt creates a hidden
contract with archon workflows. Workflows that need `repo_key` should
read it from their cwd or via a structured node, not parse it out of
the message.

**Constraints text and validation_commands** stay OC-side as the
post-execution invariant (existing pattern). They do **not** flow into
the archon message.

### D2 — Per-task conversationId; abandon on completion ✅ confirmed

**Decision:** Each `ExecutionRequest` creates a fresh conversation via
`POST /api/conversations`, runs the workflow inside it, and abandons it
on terminal status (or on timeout). 1:1 mapping ExecutionRequest ↔
Archon conversation.

**Rationale:**
- Archon conversations carry message history and context. Reusing a
  conversation across unrelated runs pollutes that history.
- The Archon Command Center treats each conversation as a user
  session. Per-task gives operators a clean "one conversation per OC
  run" model when they're debugging.
- Traceability: `ExecutionRequest.run_id` ↔ conversation `platform_conversation_id`
  is the simplest possible ID bridge; OC stores it in
  `ArchonRunCapture.metadata["archon.conversation_id"]`.
- Cost: one extra POST per run. Negligible.

**Not chosen — reused conversation:** A single OC-owned conversation
that all archon dispatches share. Cleaner conversation count, but
breaks the 1:1 trace and confuses the Command Center UI. Not worth it.

**Conversation cleanup:** After a terminal status, OC posts
`/abandon` to mark the conversation done. OC does **not** delete the
conversation — Archon's own retention policy handles that. A
conversation in `abandoned` state is harmless and queryable for
diagnostics.

### D3 — `paused` (approval gate) → `outcome="partial"`; no auto-approve in v1 ✅ confirmed

**Decision:** When a workflow run reaches terminal status `paused`,
OC's `ArchonRunResult` is:

```python
ArchonRunResult(
    outcome="partial",
    exit_code=2,                # distinct from success(0) / failure(1)
    error_text=f"archon paused for approval at node {approval.nodeId}",
    output_text=...,            # last node output, if any
    workflow_events=[...],      # full event trace
)
```

Downstream, OC's normalizer maps this to `ExecutionStatus.PARTIAL` and
surfaces a clear message to the operator. The run is **not** considered
a failure for retry/escalation purposes.

The `runId` is retained on `ArchonRunCapture.metadata["archon.run_id"]`
so operators (or future auto-approve policy) can resolve the paused
run and `/approve` or `/reject` it via Archon's CLI/dashboard.

**Rationale:**
- Approval gates exist for reasons (workflow design says human-in-the-loop
  here). OC auto-approving by default would defeat the workflow author's
  intent.
- v1 keeps the surface narrow: surface the state, let the operator decide.
- Future: a policy hook
  `archon_auto_approve: list[str]` (allowed approval-node-ids) could be
  added in v2 once we see real usage patterns.

**Not chosen v1 — auto-approve everything:** silent semantics; high
chance of running unsafe steps. Easy to add later, hard to take back.

**Not chosen v1 — treat paused as failure:** would surface as a retry
candidate, but the workflow isn't broken — it's *waiting*. Wrong signal.

### D4 — Polling, not streaming, in v1

**Decision:** Use `AsyncHttpRunner` (kickoff + poll-until-terminal) to
drive the workflow. SSE deferred.

**Rationale:**
- `AsyncHttpRunner` already exists, is tested, and matches the pattern
  exactly. Zero new infrastructure.
- Polling overhead at OC traffic levels is negligible (≤1 archon run
  in flight at a time per worker; ~2s poll interval).
- SSE adds: `httpx-sse` dep, event-stream parsing, disconnect handling,
  more fragile tests. Not worth the complexity for a marginal latency win.

**Not chosen — SSE in v1:** revisit if we ever run hundreds of
concurrent archon workflows. We're not close.

### D5 — AsyncHttpRunner integration shape (the bridge problem, resolved)

**Decision:** OC's `ArchonBackendInvoker` does the conversation
creation and run-id resolution **before** calling
`ExecutorRuntime.run()`. By the time `AsyncHttpRunner` executes, all
inputs are pure strings in `RuntimeInvocation.metadata`. The
`ManualRunner` closure pattern goes away.

**Why this works (vs. the deferral reason from 2026-05-07):** Earlier
analysis assumed the rich `ArchonWorkflowConfig` (goal_text,
constraints_text, validation_commands list, env_overrides dict) had to
flow through metadata. With Archon's actual API in hand:

- `goal_text` → `message` field, stringified into the kickoff body.
- `constraints_text` and `validation_commands` are **OC-side** (pre-flight checks
  and post-flight validation); they don't cross to archon.
- `env_overrides` is OC-side too — for archon over HTTP, env doesn't
  apply (it's archon's container env, not a subprocess env).
- `repo_path` becomes the codebaseId on the conversation create call;
  again, string.
- `metadata: dict[str, str]` is already string-typed; flows directly
  into RuntimeInvocation.metadata.

So the rich config is **prepared by the invoker** and reduced to a
string-only invocation by the time AsyncHttpRunner sees it. The
abstract `ArchonAdapter` ABC is no longer the right seam for the
production path — it stays for `StubArchonAdapter` test usage only.

### D6 — Status mapping

| Archon `run.status` | `ArchonRunResult.outcome` | `exit_code` | Notes |
|---|---|---|---|
| `completed` | `success` | `0` | Workflow finished. |
| `failed` | `failure` | `1` | Workflow errored at a node. `error_text` carries last error. |
| `cancelled` | `failure` | `1` | OC issued `/cancel` (timeout) or operator cancelled. `error_text` indicates which. |
| `paused` | `partial` | `2` | Approval gate hit. `error_text` names the node. |
| `pending` / `running` | (never terminal) | — | Polled past. |
| (timeout — OC poll deadline exceeded) | `timeout` | `null` | OC issues `/cancel` then maps. |

`workflow_events` from `GET /api/workflows/runs/{runId}` populates
`ArchonRunResult.workflow_events` for observability retention
(`BackendDetailRef` in the OC observability layer). Existing pattern.

---

## Implementation plan

### Phase A — Invoker rewrite (this design's core)

`ArchonBackendInvoker.invoke(config: ArchonWorkflowConfig)`:

1. **Pre-flight:** if base_url is unreachable (use existing
   `archon_health_probe`), return `failure` with reason — same as today.
2. **Create conversation:** `POST /api/conversations` with
   `{codebaseId: <derive from config.repo_path>}`. Capture
   `conversationId`. Failure → `failure` outcome.
3. **Resolve workflow name:** look up
   `config.workflow_type → workflow_name` from the configured map.
   Unknown → `failure` with `"unknown archon workflow: <type>"`.
4. **Build invocation:** RxP `RuntimeInvocation` with
   `runtime_kind="http_async"` and metadata:
   ```python
   {
     "http.url": f"{base_url}/api/workflows/{workflow_name}/run",
     "http.body": json.dumps({"conversationId": conv_id, "message": config.goal_text}),
     "http.body_format": "json",
     # Run-id resolution path: by-worker lookup is the canonical handle
     "http.poll_url_template": f"{base_url}/api/workflows/runs/by-worker/{conv_id}",
     # ^ once the run is registered, this returns {run: {id, status, ...}, ...}
     "http.poll_status_path": "run.status",
     "http.poll_terminal_states": "completed,failed,cancelled,paused",
     "http.poll_success_states": "completed",
     "http.poll_interval_seconds": "2.0",
     # Metadata for OC observability — never reaches Archon.
     # task_branch lives here, NOT in the message body (D1 strict).
     "archon.conversation_id": conv_id,
     "archon.workflow_name": workflow_name,
     "archon.task_branch": config.task_branch,
   }
   ```
5. **Dispatch:** `runtime.run(invocation)` → blocks until terminal.
   AsyncHttpRunner produces an RxP `RuntimeResult`.
6. **Resolve run_id:** GET the by-worker URL one final time to extract
   `run.id` and the full event list. (AsyncHttpRunner already has the
   final payload; we just need the structured fields out of it.)
7. **Build ArchonRunCapture:** populate from the final poll response —
   `run_id`, `outcome` (status mapping table above), `output_text`
   (from the last `node_completed` event with `node_output`),
   `workflow_events` (entire events list), `artifacts`, timing.
8. **On timeout:** issue `POST /api/workflows/runs/{runId}/cancel`,
   then build a `timeout` capture.
9. **On terminal:** issue `POST /api/workflows/runs/{runId}/abandon`
   for non-paused terminal states (best-effort, failure logged but
   non-fatal). For `paused` we **don't** abandon — operator may
   approve later.

### Phase B — Wire-up, tests, deprecation

- `HttpArchonAdapter.run()` becomes a thin shim over the invoker —
  signature and ABC stay, body uses the new flow. ABC kept so
  `StubArchonAdapter` continues to work for tests.
- New `tests/unit/backends/archon/test_http_workflow_integration.py`
  using `httpx.MockTransport` to script the conversation+kickoff+poll
  sequence (mirrors the `AsyncHttpRunner` test style).
- Deprecate the per-call `ManualRunner` closure path in
  `ArchonBackendInvoker` — keep it for `StubArchonAdapter` test wiring,
  but the production path uses AsyncHttpRunner. Mark the closure
  pattern as legacy in the docstring.
- `runtime_kind` in `_build_invocation` flips from `"manual"` to
  `"http_async"` for the production path.

### Phase C — Operator surface

- Add `operations-center-archon-probe` an option to `--list-workflows`
  that hits `GET /api/workflows` and prints names — operators
  cross-check that the configured workflow names exist before running.
- Emit a clear log line at archon kickoff with conversation_id and
  workflow_name so operators can find runs in the Archon Command Center.

---

## Out of scope

- **Auto-approve policy.** Surfaced as v2 work; needs separate design
  on which approval-node-ids are safe to auto-approve.
- **SSE streaming.** Deferred until polling is shown insufficient.
- **`/api/workflows/validate` integration.** Could pre-validate
  workflow YAML at config-load time; nice-to-have.
- **Retry policy for failed runs.** Existing OC recovery loop handles
  retries — archon just sees a fresh ExecutionRequest each retry.
- **Multi-conversation workflows** (worker spawning sub-conversations).
  v1 treats each ExecutionRequest as a single top-level conversation.
- **Workflow author concerns** (how to write `archon-fix-pr-dag.yaml`).
  Lives in Archon's own docs.

---

## Resolved questions

The three implementation ambiguities surfaced during design were resolved 2026-05-07:

1. **`codebaseId` semantics — omit in v1.** Archon infers from cwd or operates without it; the `createConversationBodySchema` already makes the field optional. If operators want explicit codebase registration for Command Center sidebar grouping, that's a v2 enhancement (`POST /api/codebases` at PlatformDeployment startup) — not blocking for the integration.

2. **`task_branch` propagation — strict D1, no prompt prefix.** Earlier draft suggested a one-line *"On branch {task_branch}: {goal_text}"* prefix. Rejected: that's prompt engineering by another name and weakens D1. Instead:
   - `task_branch` goes into `RuntimeInvocation.metadata` as `archon.task_branch` for OC-side observability.
   - `goal_text` reaches Archon **verbatim**.
   - If a future workflow needs branch awareness, that's a real Archon-side feature (structured variable on the workflow context, e.g. `${env.task_branch}` in YAML), not an OC frame around the operator's prompt.

3. **Workflow output synthesis — last `node_completed` event in v1; upstream issue for `workflow_completed`.** v1 synthesizes `output_text` from the last `node_completed` event's `data.node_output` field (best available signal today). A follow-up upstream Archon issue/design note will request a standardized `workflow_completed` event carrying a `result` field — once shipped, OC switches to that as the canonical output source.

---

## Effort estimate

| Phase | Rough size |
|---|---|
| A — Invoker rewrite | ~250 LOC + 200 LOC tests |
| B — Wire-up + deprecation | ~50 LOC + 100 LOC tests |
| C — Operator surface | ~50 LOC + 30 LOC tests |
| **Total** | **~700 LOC, ~1 PR** |

Sequenced as a single PR (the pieces are tightly coupled). After it
merges, the *"Switch to AsyncHttpRunner"* backlog item closes
automatically — the new invoker uses AsyncHttpRunner directly, no
ManualRunner closure on the production path.

---

## Approval status

Operator signoff received 2026-05-07:

| Item | Status |
|---|---|
| D1 — direct `goal_text` mapping, no structured prefix | ✅ confirmed (strict — also rejects task_branch prefix) |
| D2 — per-task conversation, abandon on terminal | ✅ confirmed |
| D3 — `paused` → `partial`, no auto-approve in v1 | ✅ confirmed |
| Q1 — codebaseId | resolved (omit in v1) |
| Q2 — task_branch propagation | resolved (metadata only, no prompt frame) |
| Q3 — output synthesis | resolved (last `node_completed` event; follow-up upstream Archon issue for `workflow_completed.result`) |

---

## Real-API findings (2026-05-07 live validation)

After OC #85 merged, the dispatcher was driven against a live Archon container (built from `ProtocolWarden/Archon@fd6d75e7`, deployed via `PlatformDeployment/compose/profiles/archon.yml`). All design assumptions held except three:

### F1 — Bundled-default workflow names differ from the design's table

The original table picked names like `archon-goal-default`, `archon-fix-github-issue-dag`, `archon-test-default`, `archon-improve-default`. None of those exist in `ProtocolWarden/Archon@main/.archon/workflows/defaults/`. The corrected mapping (above) uses real bundled defaults — `archon-assist`, `archon-fix-github-issue`, `archon-test-loop-dag`, `archon-refactor-safely`.

**Action taken:** updated `OperationsCenter::DEFAULT_WORKFLOW_NAMES`, `ArchonSettings.workflow_names` defaults, the `archon:` block in the gitignored `config/operations_center.local.yaml`, and the matching test fixtures.

### F2 — `GET /api/workflows` returns empty without a `?cwd=` referencing a registered codebase

The design assumed bundled defaults would surface unconditionally. They do not — Archon's discovery is cwd-scoped (per its `IWorkflowStore` model). Without `?cwd=<path-to-codebase>`, `/api/workflows` returns `{"workflows": []}` even though dispatch-by-name still works for bundled defaults.

**Implication for the operator probe (`operations-center-archon-probe --list-workflows`):** today it prints "no workflows returned" against a fresh container. That's the *correct* signal — it means the operator hasn't registered a codebase with Archon yet. A future enhancement could thread a `--cwd` flag through to the helper to enumerate workflows scoped to a specific codebase. Tracked as a v2 nice-to-have; not blocking.

### F3 — POST /run kickoff returns HTTP 200 (not 202), with `{accepted, status:"started"}`

Confirmed exactly as `ProtocolWarden/Archon@main/packages/server/src/routes/api.workflow-runs.test.ts` predicted. Drove the AsyncHttpRunner upgrade in [ER #6](https://github.com/ProtocolWarden/ExecutorRuntime/pull/6): 200 + non-terminal status falls through to poll instead of being treated as a synchronous terminal. Live-tested via the dispatcher; the kickoff was accepted, polling proceeded, and the test workflow timed out cleanly (no API key in the test container) — exercising the timeout path through to `outcome="timeout"`.

### F4 — Per-request RuntimeBinding has no native channel on stock Archon (forked 2026-05-07)

The original integration left HTTP-mode RuntimeBinding effectively dead. CLI mode honors `.archon/config.yaml` written into the worktree (G-001 mitigation), but the HTTP-mode dispatcher runs Archon in a long-running container whose cwd is fixed at startup — the worktree-config write goes nowhere the container can see, and POST /run accepts only `{conversationId, message}`.

**Action:** rather than wait on upstream, applied the patch on the **ProtocolWarden/Archon fork** per the platform's "managed forks first" pattern (SourceRegistry: *adapters first; fork when invariants can't be enforced externally*).

**Patch shape** (`ProtocolWarden/Archon@feat/per-request-runtime-override`, tracked at `OperationsCenter/patches/archon/PATCH-001.yaml`, contract gap `archon:G-005`):

| Layer | Change |
|---|---|
| `runWorkflowBodySchema` | Add optional `provider?: string`, `model?: string` |
| `HandleMessageContext` | Add `runtimeOverride?: { provider?, model? }` (readonly) |
| Route handler `/api/workflows/:name/run` | Read body fields, build `extraContext` only when set, pass to `dispatchToOrchestrator` |
| `handleMessage` → `handleWorkflowRunCommand` → `dispatchOrchestratorWorkflow` | Thread `runtimeOverride` through to the dispatcher |
| `dispatchOrchestratorWorkflow` | Apply override by mutating `workflow.provider` / `workflow.model` before any `executeWorkflow` call (mutation safe — workflow is freshly loaded per-run, discarded after dispatch) |

**OC-side wire** (in `ProtocolWarden/OperationsCenter@feat/archon-runtime-override-on-dispatch`):

- `ArchonWorkflowConfig` gains `provider: Optional[str]` and `model: Optional[str]` fields
- `ArchonBackendAdapter.execute_and_capture()` threads the existing binder's `(provider, model)` translation into the prepared config via `dataclass.replace`
- `ArchonHttpWorkflowDispatcher._build_invocation()` includes the fields in the kickoff body when set; omits them when not (preserves stock Archon compatibility for any deployment that hasn't applied PATCH-001)
- `archon.runtime_provider` and `archon.runtime_model` added to the `RuntimeInvocation.metadata` for OC-side observability (these never reach Archon)

**Backward compatibility:** stock dispatch paths (CLI / Slack / Telegram / GitHub / Discord) never set `runtimeOverride`, so they continue to behave unchanged. OC's dispatcher omits the body fields when `provider`/`model` are absent on the config, so the same OC build talks to both patched and stock Archon installations.

**Why fork rather than upstream-first:** the OC integration needed the channel to ship now; the platform pattern is to fork when invariants can't be enforced externally, then push upstream once the integration has matured enough to advocate for the API change. Upstream PR not yet filed; tracked in PATCH-001.

### What's still outstanding (out of scope for the integration PR)

- **Auto-approve policy** for paused approval gates (v2; needs a separate design on which node IDs are safe to auto-approve).
- **SSE streaming** (deferred until polling is shown insufficient at scale).
- **Operator probe `--cwd` flag** (F2 above; nice-to-have).
- **Upstream PR for F4** — file against coleam00/Archon once the override channel has weeks of real usage in OC's dispatch path. Tracked in PATCH-001 (`pushed: false`).

Implementation can proceed as a single PR per the plan above.

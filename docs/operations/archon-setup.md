# Archon Service — Local Deployment

This guide covers how PlatformDeployment runs **Archon**, the workflow harness that
OperationsCenter dispatches to via `runtime_kind="http_async"` (production
path, since OC #85) — the abstract `ArchonAdapter` ABC + ManualRunner closure
remains for `StubArchonAdapter` in tests only.

> **Status (2026-05-07):** workflow dispatch is **shipped** end-to-end — see
> [archon-real-workflow-integration.md](../architecture/adapters/archon-real-workflow-integration.md)
> for the design and `Real-API findings` section. OC #85 + CoreRunner #6
> landed the dispatcher; live-validation against a real container the same
> day surfaced two mapping corrections (now folded back).

---

## What this provides

A locally-running Archon instance reachable at `http://localhost:3000`
(or whatever `PORT_ARCHON` resolves to). OC's `ArchonHttpWorkflowDispatcher`
drives the conversation create → workflow run → poll-until-terminal →
status-mapping flow against this instance; `operations-center-archon-probe`
is the standalone health/list helper.

---

## Prerequisites

1. **Archon clone**: a sibling checkout of [ProtocolWarden/Archon][Archon] next to
   PlatformDeployment:

   ```text
   GitHub/
     PlatformDeployment/   ← this repo
     Archon/        ← git clone git@github.com:ProtocolWarden/Archon.git
   ```

   (The compose build context is `../../Archon` from `compose/`.)

2. **bun** is installed inside the Archon Dockerfile, so no host install is
   required.

3. **(Optional) PostgreSQL**: Archon defaults to SQLite. Set
   `ARCHON_DATABASE_URL` in `.env` if you want to point at a local Postgres
   container or external DB.

[Archon]: https://github.com/ProtocolWarden/Archon

---

## Starting Archon

From the PlatformDeployment repo root:

```sh
docker compose \
  -f compose/docker-compose.yml \
  -f compose/profiles/core.yml \
  -f compose/profiles/archon.yml \
  up -d archon
```

The healthcheck polls `http://localhost:3000/api/health` every 30s. The
service is considered healthy ~30s after start (Archon needs time to compile
its bun bundle on first run).

---

## Verifying

```sh
curl -fsS http://localhost:3000/api/health
# {"status": "ok"} or similar
```

From OperationsCenter:

```sh
operations-center-archon-probe                # health probe (exit 0 if healthy)
operations-center-archon-probe --list-workflows  # cross-check workflow names
```

> **Note:** `--list-workflows` will return `[FAIL] no workflows returned`
> against a fresh container until you register a codebase with Archon —
> the listing is `?cwd=`-scoped, not global. Dispatch-by-name still works
> for bundled defaults (`archon-assist`, `archon-fix-github-issue`,
> `archon-test-loop-dag`, `archon-refactor-safely`) without registration.

---

## Stopping

```sh
docker compose \
  -f compose/docker-compose.yml \
  -f compose/profiles/archon.yml \
  down archon
```

Volumes under `runtime/archon/` persist between restarts.

---

## Troubleshooting

- **Build fails with bun lockfile errors**: `git -C ../Archon pull` to make
  sure the lockfile matches the source.
- **Port collision on 3000**: set `PORT_ARCHON=3100` (or any free port) in
  `.env` at the PlatformDeployment repo root.
- **Health check failing**: `docker logs platformdeployment-archon` to see startup
  errors. First-run bundle compile can take a minute.

---

## What's deferred

- **Auto-approve policy** for paused approval gates (v2; design pending).
- **SSE streaming** (current dispatcher polls — sufficient at OC traffic levels).
- **`--cwd` flag on the probe** so `--list-workflows` can enumerate workflows scoped to a registered codebase. Today it lists empty against a fresh container. Tracked as a v2 nice-to-have.

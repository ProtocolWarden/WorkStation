# Archon Service — Local Deployment

This guide covers how WorkStation runs **Archon**, the workflow harness that
OperationsCenter dispatches to as a `runtime_kind="manual"` backend.

> **Status (2026-05-06):** the compose profile and health check are in place.
> The OC concrete `ArchonAdapter` impl currently does a **health-only probe**
> — workflow dispatch is not yet wired (the Archon API is conversation-driven
> and async; OC's integration needs design work). See backlog.

---

## What this provides

A locally-running Archon instance reachable at `http://localhost:3000` (or whatever
`PORT_ARCHON` resolves to). OC can probe `GET /api/health` to confirm reachability.
Real workflow dispatch is the **next** integration milestone, not this one.

---

## Prerequisites

1. **Archon clone**: a sibling checkout of [Velascat/Archon][Archon] next to
   WorkStation:

   ```text
   GitHub/
     WorkStation/   ← this repo
     Archon/        ← git clone git@github.com:Velascat/Archon.git
   ```

   (The compose build context is `../../Archon` from `compose/`.)

2. **bun** is installed inside the Archon Dockerfile, so no host install is
   required.

3. **(Optional) PostgreSQL**: Archon defaults to SQLite. Set
   `ARCHON_DATABASE_URL` in `.env` if you want to point at a local Postgres
   container or external DB.

[Archon]: https://github.com/Velascat/Archon

---

## Starting Archon

From the WorkStation repo root:

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
operations-center-archon-probe   # (placeholder — see backlog)
```

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
  `.env` at the WorkStation repo root.
- **Health check failing**: `docker logs workstation-archon` to see startup
  errors. First-run bundle compile can take a minute.

---

## What's deferred

The OC integration currently only probes health. Real workflow dispatch
(POST conversation → run workflow → poll/stream results → map status) is
deferred — see backlog item *"OC: real archon workflow integration"*.

# Mission Log

_Chronological continuity log. Decisions, stop points, what changed and why._
_Not a task tracker — that's objectives.md. Keep entries concise and dated._

## Recent Decisions

_Log significant choices here so they survive context resets._

| Decision | Rationale | Date |
|----------|-----------|------|
| [what was decided] | [why] | [date] |

## Stop Points

- Archon compose profile (2026-05-06, on `feat/archon-compose-profile`): Added `compose/profiles/archon.yml` following the SwitchBoard pattern — builds from sibling `Velascat/Archon` clone, exposes `PORT_ARCHON` (default 3000), mounts persistence under `runtime/archon`, health-checks `GET /api/health`. Docs at `docs/operations/archon-setup.md`. Closes the long-standing infra gap (architecture docs already said WorkStation owns archon deployment, but no compose entry existed). Companion OC PRs land a health-only concrete `ArchonAdapter` and an ER `HttpRunner` — real workflow dispatch is deferred (archon's API is conversation-driven async; needs design work, see objectives.md *"Archon real workflow integration"*).

## Notes

_Free-form scratch. Clear periodically — old entries can be deleted once no longer relevant._

---

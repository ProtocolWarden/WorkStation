# Mission Log

_Chronological continuity log. Decisions, stop points, what changed and why._
_Not a task tracker — that's backlog.md. Keep entries concise and dated._

## Recent Decisions

_Log significant choices here so they survive context resets._

| Decision | Rationale | Date |
|----------|-----------|------|
| [what was decided] | [why] | [date] |

## Stop Points

- Wire Custodian B1 privacy block (2026-05-08, on `chore/wire-b1-privacy-block`): Added top-level `privacy:` block to `.custodian/config.yaml` listing `VideoFoundry` and `videofoundry` as banned literals. B1 reports zero leaks on the public surface — defaults exclude operator-private workspaces, history docs, and the config file itself, so the block is purely declarative for now and acts as a forward guard against future leaks.

- Archon compose profile (2026-05-06, on `feat/archon-compose-profile`): Added `compose/profiles/archon.yml` following the SwitchBoard pattern — builds from sibling `Velascat/Archon` clone, exposes `PORT_ARCHON` (default 3000), mounts persistence under `runtime/archon`, health-checks `GET /api/health`. Docs at `docs/operations/archon-setup.md`. Closes the long-standing infra gap (architecture docs already said WorkStation owns archon deployment, but no compose entry existed). Companion OC PRs land a health-only concrete `ArchonAdapter` and an ER `HttpRunner` — real workflow dispatch is deferred (archon's API is conversation-driven async; needs design work, see backlog.md *"Archon real workflow integration"*).

## Notes

_Free-form scratch. Clear periodically — old entries can be deleted once no longer relevant._

---

## 2026-05-08 — M1: CHANGELOG.md stub (Keep-a-Changelog format)

Added a minimal CHANGELOG.md so M1 (and M5 format check) pass.

## 2026-05-08 — DC8: Move Quick start before Architecture


## 2026-05-08 — Custodian round: WS clean (119 → 0)

- ruff --fix --unsafe-fixes resolved 80/91 findings (T201 prints converted to
  logger calls, F401 unused imports, etc.).
- Per-file-ignores in pyproject.toml for tools/workstation_cli/** for the
  remaining 11 BLE001/S602/S110/S603 (all CLI-tool patterns: blind catch
  for user-friendly errors, shell=True for operator-supplied stop_command,
  best-effort cleanup, user-supplied subprocess targets).
- T1/T6/T7/T8/D3 exclude_paths for tools/workstation_cli/** (CLI is
  smoke-tested end-to-end, not by direct import).
- C13 allowed for local_manifest.py + config.py (config-loading layer).
- C11 timeout=86400 on the console subprocess (long interactive sessions).
- C41 ensure_ascii=False on json.dumps in lane_cli + main.
- common_words/known_values for cross-repo doc references in
  docs/architecture/adapters/ (Archon/Kodo/openclaw integrations).
- DC7: linked the 9router ADR explicitly from docs/README.md.


## 2026-05-08 — CI regression guard

Added .github/workflows/custodian-audit.yml + .hooks/pre-push.
Both run `custodian-multi --fail-on-findings`. CI is the source of
truth; pre-push catches regressions before they hit GitHub.


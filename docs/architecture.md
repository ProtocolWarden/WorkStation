# Architecture

WorkStation is the local platform host for the current stack.

```text
OperationsCenter proposes work -> SwitchBoard selects lane/backend
                           -> OperationsCenter execution boundary executes
                                       ^               ^
                                       |               |
                        WorkStation deploys services    local lane infra
```

WorkStation owns:

- SwitchBoard deployment and health checks
- local lane infrastructure for `aider_local`
- endpoint/status configuration
- compose scripts and operator utilities

Current reference docs:

- [`docs/architecture/system/system_overview.md`](architecture/system/system_overview.md)
- [`docs/architecture/system/repo_responsibility_matrix.md`](architecture/system/repo_responsibility_matrix.md)
- [`docs/architecture/system/ownership.md`](architecture/system/ownership.md)

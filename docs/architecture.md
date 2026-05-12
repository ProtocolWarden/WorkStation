# Architecture

PlatformDeployment is the current repository identity for the
`PlatformDeployment` plane of the stack.

```text
OperationsCenter proposes work -> SwitchBoard selects lane/backend
                           -> OperationsCenter execution boundary executes
                                       ^               ^
                                       |               |
                PlatformDeployment deploys services     local lane infra
```

PlatformDeployment owns:

- SwitchBoard deployment and health checks
- local lane infrastructure for `aider_local`
- endpoint/status configuration
- compose scripts and operator utilities

PlatformDeployment does not own:

- platform ontology
- public topology language
- private topology truth
- orchestration policy

Current reference docs:

- [`docs/architecture/system/system_overview.md`](architecture/system/system_overview.md)
- [`docs/architecture/system/repo_responsibility_matrix.md`](architecture/system/repo_responsibility_matrix.md)
- [`docs/architecture/system/ownership.md`](architecture/system/ownership.md)

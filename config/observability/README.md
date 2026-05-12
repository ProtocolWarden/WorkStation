# Observability profile config

Configuration files mounted by `compose/profiles/observability.yml`
into the Prometheus and Grafana containers.

## Layout

```text
config/observability/
├── prometheus.yml                      # Prometheus scrape config
└── grafana/provisioning/datasources/
    └── prometheus.yaml                  # Grafana auto-provisioned datasource
```

## Why these ship in the repo

Earlier versions of the observability profile mounted from
`../../config/observability/` (sibling-of-PlatformDeployment, outside the
repo). On a clean machine those paths didn't exist, so Docker
auto-created them as root-owned directories — which then permanently
broke the next `up` of the prometheus container with the cryptic
`failed to mount: not a directory` error.

Shipping the skeleton in-repo means a fresh clone of PlatformDeployment
boots the observability profile without any manual setup or sudo.

## Operator overrides

If you need machine-specific changes (e.g. additional scrape jobs,
custom retention, Grafana auth), the simplest pattern is a compose
override file (`docker-compose.override.yml`) that re-mounts these
paths from a private location. The shipped skeleton stays the
sensible default; your override stays out of git.

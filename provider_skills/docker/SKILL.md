# Docker Provider Operations Skill

Local/remote container operations — stub until implemented.

## Supported operations

- containers (stub)
- compose services (stub)
- logs (stub)
- restart (stub)
- rebuild (stub)
- health (stub)

## Required credentials

- Docker host access via governed executor

## Readonly tools

- container_logs
- compose_ps

## Mutation tools

- container_restart (not implemented)
- compose_up (not implemented)

## Evidence rules

- Capture container exit codes and healthcheck output.

## Verification rules

- Healthcheck passing after restart required.

## Rollback rules

- Not implemented.

## Common failure patterns

- Host executor disabled

## Repair recipes

- Enable governed executor, rerun readonly inspect

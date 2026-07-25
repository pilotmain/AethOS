# AWS Provider Operations Skill

IAM-scoped cloud operations — stub until implemented.

## Supported operations

- ECS services (stub)
- Lambda functions (stub)
- CloudWatch logs (stub)
- EKS deployments (stub)
- restart/redeploy equivalents (stub)

## Required credentials

- AWS access key, secret, region with least-privilege IAM

## Readonly tools

- cloudwatch_logs
- ecs_describe
- lambda_get

## Mutation tools

- ecs_update_service (not implemented)
- lambda_update (not implemented)

## Evidence rules

- CloudWatch log streams must be filtered after approval time.

## Verification rules

- Service steady state + post-approval logs required.

## Rollback rules

- Not implemented.

## Common failure patterns

- IAM scope too broad or too narrow

## Repair recipes

- Fix IAM policy, rerun readonly describe + logs

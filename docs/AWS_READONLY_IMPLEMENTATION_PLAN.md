# AWS Readonly Implementation Plan

**Sprint:** FUNCTIONALITY_REALITY_SPRINT_001 (P4)

## Phase 1 (this sprint)

- Register AWS in `ProviderRegistry` with readonly capability flags
- `AwsAuthAdapter` + credential gate hook
- Catalog shows **Disconnected** (not Coming soon) when registered

## Phase 2 (next)

1. Credential schema (access key + secret via vault)
2. `boto3` readonly adapter:
   - `sts:GetCallerIdentity`
   - `ec2:DescribeRegions`
   - `ecs:ListServices`
   - `lambda:ListFunctions`
   - `apigateway:GetRestApis`
   - `logs:DescribeLogGroups`
3. Connections UI connect/validate
4. Readonly health report job type
5. Redaction policy on all responses

## Non-Goals

No ECS deploy, Lambda publish, or IAM mutation in phase 2.

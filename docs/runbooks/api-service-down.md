# APIServiceDown Runbook

## Alert
**Name**: APIServiceDown
**Severity**: P0
**Fires when**: ECS service `selfpublisherforge-api-production` has zero running tasks for more than 5 minutes.

## Impact
The API service is completely unavailable. All user-facing requests will fail. Users cannot access the application at all. This is a total service outage.

## Investigation Steps
1. Check the ECS console for the `selfpublisherforge-api-production` service. Look at the "Tasks" tab to see if tasks are being launched and failing, or if no tasks are being scheduled at all.
2. Review ECS service events for error messages (e.g., insufficient capacity, image pull failures, container health check failures). Run: `aws ecs describe-services --cluster selfpublisherforge-production --services selfpublisherforge-api-production`.
3. Check CloudWatch Logs for the most recent task's container logs to identify crash reasons (OOM kills, application exceptions, dependency failures).
4. Verify that dependent services (RDS, Redis, Elasticsearch) are healthy and reachable from the ECS cluster's VPC.
5. Check if a recent deployment triggered the issue by reviewing the deployment history: `aws ecs describe-services --cluster selfpublisherforge-production --services selfpublisherforge-api-production | jq '.services[0].deployments'`.

## Resolution
### Common Causes
- **Bad deployment / application crash**: Roll back to the previous task definition revision using `aws ecs update-service --cluster selfpublisherforge-production --service selfpublisherforge-api-production --task-definition <previous-revision>`.
- **Container image pull failure**: Verify the ECR image exists and the ECS task execution role has permission to pull it. Check ECR repository and IAM policies.
- **Out of memory (OOM) kill**: Increase the memory limits in the task definition or identify and fix the memory leak in the application.
- **Health check failure**: Review the health check endpoint (`/health`) to ensure it responds correctly. Check application startup time versus health check grace period.
- **Infrastructure capacity**: Ensure the ECS cluster has sufficient capacity (Fargate limits, EC2 instances) to schedule tasks.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Implement canary deployments with automatic rollback on health check failures.
- Set appropriate health check grace periods to allow for application startup time.
- Configure ECS circuit breaker to automatically roll back failed deployments.
- Maintain sufficient memory and CPU headroom in task definitions.
- Run pre-deployment smoke tests in staging before promoting to production.

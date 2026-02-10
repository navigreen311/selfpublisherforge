# APIErrorRateCritical Runbook

## Alert
**Name**: APIErrorRateCritical
**Severity**: P0
**Fires when**: The API 5xx error rate exceeds 5% of total requests over a 5-minute window, sustained for 5 minutes.

## Impact
More than 5% of all API requests are failing with server errors. A significant number of users are experiencing failures. Core functionality such as book publishing, account management, and data retrieval may be broken.

## Investigation Steps
1. Check application logs in CloudWatch for the most frequent 5xx errors. Filter by status code 500, 502, 503, and 504 to identify the failing endpoints and error messages.
2. Identify whether the errors are concentrated on specific endpoints or spread across all endpoints. Run queries against the access logs to group error counts by path.
3. Check dependent service health: RDS (connection count, CPU), Redis (connectivity, memory), Elasticsearch (cluster health). A downstream dependency failure is a common cause of elevated 5xx rates.
4. Review recent deployments. If a deployment occurred within the last 30 minutes, it is likely the root cause. Check the deployment timeline against the error rate spike.
5. Look at ECS task health and resource utilization (CPU, memory) to rule out resource exhaustion causing request failures.

## Resolution
### Common Causes
- **Bad deployment**: Roll back to the previous task definition if errors started after a deployment. Use `aws ecs update-service` with the previous task definition revision.
- **Database overload or unavailability**: If RDS is the bottleneck, check for long-running queries, connection exhaustion, or instance health. Kill long-running queries and consider read replicas.
- **Upstream dependency failure**: If a third-party API or internal microservice is failing, enable circuit breakers or fallback behavior. Check the status pages of external dependencies.
- **Memory or CPU exhaustion**: If ECS tasks are resource-constrained, requests may time out or crash. Scale up task count or increase resource limits.
- **Application bug**: If the error is in application code, identify the exception from logs, fix, and deploy a hotfix.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Implement canary deployments to catch errors before full rollout.
- Add circuit breakers for downstream service calls.
- Ensure comprehensive error handling and graceful degradation in the application.
- Run load tests against staging to validate changes before production deployment.
- Set up the P1 elevated-error-rate alert (1% threshold) to catch issues before they reach the 5% critical level.

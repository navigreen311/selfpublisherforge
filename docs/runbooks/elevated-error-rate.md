# APIErrorRateWarning Runbook

## Alert
**Name**: APIErrorRateWarning
**Severity**: P1
**Fires when**: The API 5xx error rate exceeds 1% of total requests over a 10-minute window, sustained for 10 minutes.

## Impact
The API error rate has exceeded the 1% SLO threshold. While the majority of requests are succeeding, a meaningful number of users are encountering errors. If left unaddressed, this may escalate to the P0 critical error rate alert (5%).

## Investigation Steps
1. Check application logs in CloudWatch for 5xx errors. Filter by time range and identify the most frequent error types and affected endpoints.
2. Determine if errors are isolated to specific endpoints, specific users, or specific request types. This helps narrow the root cause.
3. Check if a recent deployment correlates with the error rate increase. Review the deployment timeline and diff the changes.
4. Verify health of downstream dependencies: RDS (connection count, CPU, replication lag), Redis (connectivity, memory), Elasticsearch (cluster health), and any external APIs.
5. Check ECS task health and container logs for OOM kills, crash loops, or resource throttling.

## Resolution
### Common Causes
- **Partial deployment failure**: If some tasks are running a bad version while others are healthy, complete the rollback to ensure all tasks run the last known good version.
- **Intermittent dependency issues**: A flapping downstream service (database, cache, external API) can cause intermittent errors. Identify the failing dependency and address its health issue.
- **Resource contention**: If ECS tasks are near their CPU or memory limits, some requests may fail under load. Scale out the service or increase task resource limits.
- **Rate limiting or throttling**: If an external dependency is throttling requests, implement backoff and retry logic or increase rate limits.
- **Data-dependent errors**: Specific data conditions (e.g., malformed user data, edge cases) may cause errors for a subset of requests. Identify the pattern from error logs and add defensive handling.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Implement comprehensive error handling and graceful degradation in the application.
- Use canary deployments to catch regressions before they affect all users.
- Add circuit breakers for downstream service calls to prevent cascading failures.
- Monitor error rates continuously and set up dashboards for quick visual identification of trends.
- Ensure thorough testing (unit, integration, load) before deploying to production.

# APILatencyP95Warning Runbook

## Alert
**Name**: APILatencyP95Warning
**Severity**: P2
**Fires when**: The API P95 latency exceeds 500ms (the SLO target) over a 15-minute window, sustained for 15 minutes.

## Impact
The application is not meeting its latency SLO. Users are experiencing slower-than-expected response times. While the service is functional, the degraded performance may affect user satisfaction and engagement. If left unaddressed, this may escalate to the P1 critical latency alert (2 seconds).

## Investigation Steps
1. Identify the slowest endpoints by reviewing access logs or APM traces. Determine if the latency is widespread or concentrated on specific routes.
2. Check database query performance. Run slow query analysis and look for queries exceeding 100ms: `SELECT query, mean_exec_time, calls FROM pg_stat_statements WHERE mean_exec_time > 100 ORDER BY mean_exec_time DESC LIMIT 20;`.
3. Check Redis cache hit rate and latency. A drop in cache hit rate forces more requests to the database, increasing overall latency.
4. Review ECS task CPU and memory utilization. Resource-constrained tasks process requests more slowly.
5. Check for any recent code changes, deployments, or infrastructure modifications that correlate with the latency increase.

## Resolution
### Common Causes
- **Slow database queries**: Optimize queries by adding indexes, rewriting joins, or caching results. Use `EXPLAIN ANALYZE` to identify full table scans or inefficient query plans.
- **Cache cold start or low hit rate**: If the cache was recently flushed or a new feature bypasses caching, the database bears extra load. Ensure proper caching is in place and allow the cache to warm up.
- **Insufficient compute resources**: If ECS tasks are CPU-throttled, scale out the service or increase task CPU allocation.
- **N+1 query patterns**: A code change may have introduced an N+1 query pattern where the application makes many small database queries instead of one efficient query. Identify and batch these queries.
- **External API latency**: If the application calls external APIs synchronously, their latency directly affects response times. Add timeouts and consider asynchronous processing.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Establish latency budgets per endpoint and monitor them continuously.
- Implement query performance monitoring and automated slow query alerts.
- Use caching effectively at multiple layers (application, CDN, Redis).
- Conduct regular load testing to identify latency regressions before they reach production.
- Add latency SLO checks to the CI/CD pipeline for performance-critical endpoints.

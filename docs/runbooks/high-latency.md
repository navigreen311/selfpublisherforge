# APILatencyP95Critical Runbook

## Alert
**Name**: APILatencyP95Critical
**Severity**: P1
**Fires when**: The API P95 latency exceeds 2 seconds over a 10-minute window, sustained for 10 minutes.

## Impact
Users are experiencing significant slowness across the application. Page loads, API calls, and background operations are all taking much longer than normal. While the service is not down, user experience is severely degraded and some requests may time out.

## Investigation Steps
1. Identify which endpoints have the highest latency. Check application access logs or APM dashboards to find the slowest endpoints and determine if the latency is concentrated or widespread.
2. Check RDS performance metrics: CPU utilization, read/write latency, connection count, and active queries. Slow database queries are the most common cause of API latency spikes. Run `SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC LIMIT 20;`.
3. Check Redis latency and connection metrics. A slow or unreachable Redis cache will cause the application to fall through to the database for every request.
4. Review ECS task CPU and memory utilization. If tasks are resource-constrained, request processing will slow down.
5. Check for any ongoing deployments, auto-scaling events, or infrastructure changes that correlate with the latency increase.

## Resolution
### Common Causes
- **Slow database queries**: Identify and optimize the slow queries. Add missing indexes, rewrite inefficient queries, or add caching. Use `EXPLAIN ANALYZE` to understand query plans.
- **Database resource exhaustion**: If RDS CPU is high, consider scaling up the instance class, adding read replicas, or optimizing query patterns.
- **Cache misses (Redis down or cold cache)**: If Redis is unavailable or was recently flushed, the database will be overloaded with requests that should be cached. Restore Redis and allow the cache to warm up.
- **Insufficient ECS task count**: If traffic has increased beyond the capacity of running tasks, scale out the service: `aws ecs update-service --cluster selfpublisherforge-production --service selfpublisherforge-api-production --desired-count <new-count>`.
- **Network latency or DNS issues**: Check for VPC networking issues, NAT gateway throttling, or DNS resolution delays.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Implement query performance monitoring and alerting on slow queries.
- Maintain proper database indexes and run `ANALYZE` regularly.
- Configure auto-scaling policies for ECS services based on CPU and request count.
- Use caching effectively to reduce database load.
- Conduct regular load testing to identify performance bottlenecks before they affect production.

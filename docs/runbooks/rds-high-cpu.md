# RDSCPUCritical Runbook

## Alert
**Name**: RDSCPUCritical
**Severity**: P1
**Fires when**: RDS CPU utilization on `selfpublisherforge-production-postgres` exceeds 90%, sustained for 10 minutes.

## Impact
Database performance is likely degraded. Queries will take longer to execute, which increases API latency. If CPU remains saturated, connections may time out and the application may start returning errors. This can cascade into API error rate alerts.

## Investigation Steps
1. Check the current RDS CPU utilization in CloudWatch and identify when the spike started. Correlate with any deployments, cron jobs, or traffic spikes.
2. Identify expensive queries currently running on the database: `SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC LIMIT 20;`.
3. Check for queries with high CPU consumption using `pg_stat_statements`: `SELECT query, calls, mean_exec_time, total_exec_time FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 20;`.
4. Look for missing indexes. Check if recently added queries or features introduced full table scans.
5. Review connection count to see if connection storms are contributing to CPU load.

## Resolution
### Common Causes
- **Expensive or unoptimized queries**: Identify the slow queries and optimize them. Add indexes, rewrite queries, or add caching to reduce database load. Use `EXPLAIN ANALYZE` to diagnose query plans.
- **Missing database indexes**: Add indexes for columns used in WHERE clauses, JOINs, and ORDER BY. Run `EXPLAIN` on slow queries to confirm index usage.
- **Lock contention**: Check for lock waits: `SELECT * FROM pg_locks WHERE NOT granted;`. Long-held locks cause other queries to queue up, increasing overall CPU.
- **Autovacuum running on large tables**: Autovacuum can consume significant CPU. Check `pg_stat_progress_vacuum` for active vacuum operations. Consider tuning autovacuum settings.
- **Traffic spike or batch operation**: If legitimate traffic has increased, scale up the RDS instance class or add read replicas to distribute the load.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Monitor slow query logs and address performance issues proactively.
- Run `ANALYZE` regularly to keep query planner statistics up to date.
- Implement query-level caching (Redis) for frequently accessed, read-heavy data.
- Use read replicas for reporting and analytics queries to offload the primary instance.
- Right-size the RDS instance class for the workload and plan for capacity growth.

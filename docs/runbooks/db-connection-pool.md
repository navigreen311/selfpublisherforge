# DBConnectionPoolNearCapacity Runbook

## Alert
**Name**: DBConnectionPoolNearCapacity
**Severity**: P2
**Fires when**: The database connection count on `selfpublisherforge-production-postgres` exceeds 150 (max 200), sustained for 10 minutes.

## Impact
The database connection pool is approaching its maximum capacity. When the limit is reached, new connection attempts will be rejected, causing application errors. Services that need new database connections will fail, leading to 5xx errors for users.

## Investigation Steps
1. Check the current connection count and breakdown by application/user: `SELECT usename, application_name, client_addr, count(*) FROM pg_stat_activity GROUP BY usename, application_name, client_addr ORDER BY count(*) DESC;`.
2. Identify idle connections that may be leaking: `SELECT pid, usename, application_name, state, state_change, query FROM pg_stat_activity WHERE state = 'idle' ORDER BY state_change ASC LIMIT 20;`.
3. Check if a specific service or deployment is opening more connections than expected. Correlate connection growth with recent deployments or scaling events.
4. Review the application's connection pool configuration (e.g., SQLAlchemy pool size, max overflow) and compare against the number of running ECS tasks.
5. Check if ECS auto-scaling has increased the task count, which multiplies the total number of database connections.

## Resolution
### Common Causes
- **Connection leak in application code**: Connections are being opened but not properly returned to the pool. Review recent code changes for missing connection cleanup (e.g., `session.close()`, context manager usage). Restart affected ECS tasks as an immediate fix.
- **Too many ECS tasks with large pool sizes**: If each ECS task opens a pool of connections, scaling the service multiplies total connections. Reduce per-task pool size or implement a connection pooler.
- **Idle connections accumulating**: Long-lived idle connections consuming slots. Configure `idle_in_transaction_session_timeout` and `statement_timeout` in PostgreSQL to automatically close stale connections.
- **Batch jobs or migrations holding connections**: A background job or database migration may be holding many connections. Identify and terminate the offending process if appropriate.
- **Missing connection pooler**: Without a connection pooler like PgBouncer, each application process maintains its own connections. Deploy PgBouncer as a sidecar or standalone service.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Deploy PgBouncer as a connection pooler between the application and the database.
- Configure appropriate pool sizes per ECS task (e.g., `pool_size=5`, `max_overflow=5`) and calculate the maximum total connections based on expected task count.
- Set PostgreSQL `idle_in_transaction_session_timeout` to automatically terminate idle transactions.
- Monitor connection count trends and adjust pool settings when scaling services.
- Increase the RDS `max_connections` parameter if the current limit is too low for the workload, or scale to a larger instance class.

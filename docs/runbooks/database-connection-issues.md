# Runbook: Database Connection Issues

## Alert

| Field       | Value                                                                                        |
|-------------|----------------------------------------------------------------------------------------------|
| Alert Name  | `DatabaseConnectionFailure` (P0) / `DBConnectionPoolNearCapacity` (P2)                      |
| Expression  | `pg_up{instance=~"selfpublisherforge-production-postgres.*"} == 0` (P0, 2m) or `pg_stat_activity_count > 150` (P2, 10m) |
| Severity    | **P0 -- Critical** (database unreachable) / **P2 -- Warning** (connection pool near capacity)|
| Service     | `database`                                                                                   |
| Environment | `production`                                                                                 |
| Runbook URL | `docs/runbooks/rds-connection-failure.md` (P0) / `docs/runbooks/db-connection-pool.md` (P2)  |

This runbook covers two scenarios:
1. **DatabaseConnectionFailure (P0)**: The postgres_exporter reports `pg_up == 0`, meaning the RDS instance is completely unreachable. Database operations will fail.
2. **DBConnectionPoolNearCapacity (P2)**: Active connections exceed 150 out of a maximum of 200. Connection exhaustion is approaching.

## Impact

### Database unreachable (P0)
- **Complete service outage.** All read and write operations fail.
- API returns 500 errors on every request that touches the database.
- Background workers fail on all database-dependent tasks.
- User data is inaccessible. No books can be created, published, or retrieved.

### Connection pool near capacity (P2)
- New database connections may be refused once the 200-connection limit is reached.
- Increased latency as connections queue waiting for availability.
- Intermittent 500 errors on endpoints requiring new database connections.
- If unchecked, will escalate to a P0 when connections are fully exhausted.

## Investigation

### 1. Check RDS instance status

```bash
# Check the RDS instance status, endpoint, and configuration
aws rds describe-db-instances \
  --db-instance-identifier selfpublisherforge-production-postgres \
  --query 'DBInstances[0].{
    Status: DBInstanceStatus,
    Engine: Engine,
    EngineVersion: EngineVersion,
    InstanceClass: DBInstanceClass,
    MultiAZ: MultiAZ,
    Endpoint: Endpoint.Address,
    Port: Endpoint.Port,
    AllocatedStorage: AllocatedStorage,
    FreeStorage: FreeStorageSpace
  }'

# Check recent RDS events (maintenance, failovers, restarts)
aws rds describe-events \
  --source-identifier selfpublisherforge-production-postgres \
  --source-type db-instance \
  --duration 120 \
  --query 'Events[].{Date:Date,Message:Message}' \
  --output table
```

### 2. Test direct connectivity

```bash
# Test TCP connectivity to the RDS endpoint
nc -zv <rds-endpoint> 5432

# Test DNS resolution
nslookup <rds-endpoint>

# Test a simple query (from bastion or container in the same VPC)
psql -h <rds-endpoint> -U selfpublisherforge -d selfpublisherforge_production \
  -c "SELECT 1 AS connectivity_check;"

# Check the PostgreSQL server version and uptime
psql -h <rds-endpoint> -U selfpublisherforge -d selfpublisherforge_production \
  -c "SELECT version(), pg_postmaster_start_time(), now() - pg_postmaster_start_time() AS uptime;"
```

### 3. Inspect pg_stat_activity

```bash
psql -h <rds-endpoint> -U selfpublisherforge -d selfpublisherforge_production <<'SQL'
-- Total connection count grouped by state
SELECT state, count(*)
FROM pg_stat_activity
GROUP BY state
ORDER BY count DESC;

-- Connections grouped by application name and client address
SELECT application_name, client_addr, state, count(*)
FROM pg_stat_activity
GROUP BY application_name, client_addr, state
ORDER BY count DESC;

-- Long-running active queries (potential connection hogs)
SELECT
  pid,
  now() - query_start AS duration,
  state,
  left(query, 100) AS query_preview
FROM pg_stat_activity
WHERE (now() - query_start) > interval '5 minutes'
  AND state = 'active'
ORDER BY duration DESC;

-- Idle connections held open for a long time
SELECT
  pid,
  now() - state_change AS idle_duration,
  application_name,
  client_addr
FROM pg_stat_activity
WHERE state = 'idle'
  AND (now() - state_change) > interval '10 minutes'
ORDER BY idle_duration DESC;

-- Check max_connections setting
SHOW max_connections;
SQL
```

### 4. Check for lock contention

```bash
psql -h <rds-endpoint> -U selfpublisherforge -d selfpublisherforge_production <<'SQL'
-- Find blocked queries and what is blocking them
SELECT
  blocked.pid AS blocked_pid,
  blocked.usename AS blocked_user,
  left(blocked.query, 80) AS blocked_query,
  blocking.pid AS blocking_pid,
  blocking.usename AS blocking_user,
  left(blocking.query, 80) AS blocking_query,
  now() - blocked.query_start AS blocked_duration
FROM pg_catalog.pg_locks bl
JOIN pg_catalog.pg_stat_activity blocked ON blocked.pid = bl.pid
JOIN pg_catalog.pg_locks bgl
  ON bgl.locktype = bl.locktype
  AND bgl.database IS NOT DISTINCT FROM bl.database
  AND bgl.relation IS NOT DISTINCT FROM bl.relation
  AND bgl.page IS NOT DISTINCT FROM bl.page
  AND bgl.tuple IS NOT DISTINCT FROM bl.tuple
  AND bgl.virtualxid IS NOT DISTINCT FROM bl.virtualxid
  AND bgl.transactionid IS NOT DISTINCT FROM bl.transactionid
  AND bgl.classid IS NOT DISTINCT FROM bl.classid
  AND bgl.objid IS NOT DISTINCT FROM bl.objid
  AND bgl.objsubid IS NOT DISTINCT FROM bl.objsubid
  AND bgl.pid != bl.pid
JOIN pg_catalog.pg_stat_activity blocking ON blocking.pid = bgl.pid
WHERE NOT bl.granted
ORDER BY blocked_duration DESC;
SQL
```

### 5. Check RDS performance metrics

```bash
# RDS CPU utilization (last 30 minutes)
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=selfpublisherforge-production-postgres \
  --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum

# Freeable memory
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name FreeableMemory \
  --dimensions Name=DBInstanceIdentifier,Value=selfpublisherforge-production-postgres \
  --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average

# Database connections count over time
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=selfpublisherforge-production-postgres \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum

# Read and write IOPS
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name ReadIOPS \
  --dimensions Name=DBInstanceIdentifier,Value=selfpublisherforge-production-postgres \
  --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average
```

### 6. Check application-side connection pool configuration

```bash
# Check the task definition for database pool environment variables
aws ecs describe-task-definition \
  --task-definition spf-api \
  --query 'taskDefinition.containerDefinitions[0].environment[?
    name==`DATABASE_POOL_SIZE` ||
    name==`DATABASE_MAX_OVERFLOW` ||
    name==`DATABASE_POOL_TIMEOUT` ||
    name==`DATABASE_URL`
  ].{name:name,value:value}'
```

## Resolution

### RDS instance is down or unreachable

1. Check the RDS instance status from step 1 above.
2. Common statuses and actions:
   - **`backing-up`**: Wait for the backup to complete (typically under 5 minutes).
   - **`modifying`**: Wait for the modification. Identify who initiated it.
   - **`rebooting`**: Wait for the reboot. Should complete within a few minutes.
   - **`failed`**: Contact AWS Support immediately (Severity 1 case).
   - **`storage-full`**: See `rds-storage-critical.md`.

3. If the instance is `available` but unreachable, check networking:
   ```bash
   # Check security group rules
   aws ec2 describe-security-groups \
     --group-ids <rds-security-group-id> \
     --query 'SecurityGroups[0].IpPermissions[?FromPort==`5432`]'

   # Check subnet route tables
   aws ec2 describe-route-tables \
     --filters Name=association.subnet-id,Values=<rds-subnet-id>
   ```

4. For Multi-AZ failover: DNS should auto-resolve to the new primary. Verify DNS has propagated:
   ```bash
   dig +short <rds-endpoint>
   ```

### Connection pool exhaustion (>150 connections)

1. **Immediate relief** -- terminate long-idle connections:
   ```sql
   -- Kill connections idle for more than 30 minutes
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE state = 'idle'
     AND (now() - state_change) > interval '30 minutes'
     AND pid != pg_backend_pid();
   ```

2. **Kill long-running queries** holding connections:
   ```sql
   -- Terminate queries running longer than 10 minutes
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE (now() - query_start) > interval '10 minutes'
     AND state = 'active'
     AND pid != pg_backend_pid();
   ```

3. **Restart API tasks** to reset all application-level connection pools:
   ```bash
   aws ecs update-service \
     --cluster selfpublisherforge-production \
     --service spf-api \
     --force-new-deployment
   ```

4. **Also restart workers** if they hold database connections:
   ```bash
   aws ecs update-service \
     --cluster selfpublisherforge-production \
     --service spf-celery-worker \
     --force-new-deployment
   ```

### Lock contention causing connection buildup

1. Identify the blocking query from step 4 above.
2. Terminate the blocking process:
   ```sql
   SELECT pg_terminate_backend(<blocking_pid>);
   ```
3. Investigate why the lock was held (long-running migrations, bulk updates, missing indexes).

### Long-term improvements

- Deploy PgBouncer as a connection pooler between the application and RDS to manage connections more efficiently.
- Tune `POOL_SIZE` and `MAX_OVERFLOW` in the application configuration.
- Add statement timeouts (`SET statement_timeout = '30s'`) to prevent runaway queries.
- Set `idle_in_transaction_session_timeout` on the database to auto-kill idle transactions.
- Review query performance and add missing indexes for slow queries.

## Escalation

| Condition                                           | Escalate To                              |
|-----------------------------------------------------|------------------------------------------|
| RDS status is `failed` or instance unreachable      | AWS Support (Severity 1) + Engineering Lead |
| Connection pool exhausted, cause unknown             | Database Lead                            |
| Suspected data corruption                            | Database Lead + CTO                      |
| Unable to restore connectivity within 10 minutes    | Engineering Lead                         |
| Lock contention from unknown source                  | Database Lead                            |
| Customer-visible outage exceeding 15 minutes         | VP Engineering + CTO                     |

### Communication

- Post in `#incidents` with the database status and impact scope.
- If full database outage: update the status page immediately.
- Coordinate with the Database Lead for any manual SQL interventions.
- After resolution, create a post-incident review document.

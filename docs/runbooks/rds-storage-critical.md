# RDSStorageSpaceCritical Runbook

## Alert
**Name**: RDSStorageSpaceCritical
**Severity**: P0
**Fires when**: RDS free storage space on `selfpublisherforge-production-postgres` falls below 2 GB for more than 5 minutes.

## Impact
The database is at imminent risk of running out of storage. When storage is fully exhausted, the database becomes read-only and all write operations will fail. This will cause application-wide failures for any operation that writes data (user signups, content publishing, settings changes, etc.).

## Investigation Steps
1. Check current free storage space: `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name FreeStorageSpace --dimensions Name=DBInstanceIdentifier,Value=selfpublisherforge-production-postgres --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) --end-time $(date -u +%Y-%m-%dT%H:%M:%S) --period 300 --statistics Average`.
2. Identify the largest tables and their growth rate by connecting to the database and running: `SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 20;`.
3. Check for bloated tables that need vacuuming: `SELECT relname, n_dead_tup, last_autovacuum FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 20;`.
4. Look for unexpectedly large WAL files or temporary files consuming storage.
5. Check if storage auto-scaling is enabled and if it has reached its maximum limit.

## Resolution
### Common Causes
- **Organic data growth without capacity planning**: Increase the allocated storage immediately: `aws rds modify-db-instance --db-instance-identifier selfpublisherforge-production-postgres --allocated-storage <new-size> --apply-immediately`. Note: RDS storage can only be increased, not decreased.
- **Table bloat from lack of vacuuming**: Run `VACUUM FULL` on the most bloated tables (note: this locks the table). For less disruptive cleanup, run standard `VACUUM` and ensure autovacuum is configured properly.
- **Excessive logging or WAL retention**: Review the `rds.log_retention_period` and WAL settings. Reduce retention if logs are consuming excessive space.
- **Large temporary tables or queries**: Identify and terminate queries generating excessive temporary data. Check `pg_stat_activity` for long-running queries.
- **Uncleared old backups or snapshots consuming space**: While RDS snapshots don't use instance storage, ensure no application-level backup files are stored on the instance.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Enable RDS storage auto-scaling with an appropriate maximum storage threshold.
- Set up the P2 `RDSFreeStorageLow` alert (10 GB threshold) to catch storage trends before they become critical.
- Implement a data retention policy to archive or delete old data.
- Schedule regular `VACUUM ANALYZE` operations and ensure autovacuum is properly tuned.
- Monitor storage growth trends weekly and plan capacity increases proactively.

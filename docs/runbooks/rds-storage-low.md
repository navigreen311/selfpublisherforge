# RDSFreeStorageLow Runbook

## Alert
**Name**: RDSFreeStorageLow
**Severity**: P2
**Fires when**: RDS free storage space on `selfpublisherforge-production-postgres` falls below 10 GB, sustained for 15 minutes.

## Impact
Database storage is running low. While the database is still functioning normally, continued growth without intervention will eventually lead to the P0 critical storage alert (2 GB) and potential database read-only mode. This is an early warning to take action before the situation becomes critical.

## Investigation Steps
1. Check current free storage and the rate of consumption: review the `FreeStorageSpace` CloudWatch metric over the last 24 hours and 7 days to understand the trend.
2. Identify the largest tables and indexes: `SELECT schemaname, relname, pg_size_pretty(pg_total_relation_size(relid)) AS total_size FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 20;`.
3. Check for table bloat that could be reclaimed with vacuuming: `SELECT relname, n_dead_tup, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_stat_user_tables WHERE n_dead_tup > 10000 ORDER BY n_dead_tup DESC;`.
4. Review if storage auto-scaling is enabled and its current configuration: `aws rds describe-db-instances --db-instance-identifier selfpublisherforge-production-postgres --query 'DBInstances[0].MaxAllocatedStorage'`.
5. Check for large, unnecessary data that can be archived or deleted (old logs, expired sessions, soft-deleted records past retention period).

## Resolution
### Common Causes
- **Natural data growth**: Increase allocated storage: `aws rds modify-db-instance --db-instance-identifier selfpublisherforge-production-postgres --allocated-storage <new-size> --apply-immediately`. Plan for 3-6 months of growth.
- **Table bloat**: Run `VACUUM` on bloated tables to reclaim space from dead tuples. For severe bloat, schedule a maintenance window for `VACUUM FULL` (requires table lock).
- **Unnecessary data retention**: Implement or enforce data retention policies. Archive old records to S3 and delete them from the database.
- **Excessive indexes**: Review and drop unused indexes. Use `pg_stat_user_indexes` to identify indexes with zero or very low usage.
- **WAL accumulation**: If WAL files are accumulating, check replication status and ensure WAL archiving is functioning correctly.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Enable RDS storage auto-scaling with an appropriate maximum storage threshold.
- Implement and enforce data retention policies with automated cleanup jobs.
- Monitor storage growth trends and project when additional capacity will be needed.
- Tune autovacuum to run more frequently on high-churn tables.
- Schedule regular reviews of database size and growth patterns.

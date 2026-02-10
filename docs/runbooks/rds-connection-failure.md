# DatabaseConnectionFailure Runbook

## Alert
**Name**: DatabaseConnectionFailure
**Severity**: P0
**Fires when**: No active database connections are detected on the `selfpublisherforge-production-postgres` RDS instance for more than 3 minutes.

## Impact
The database is unreachable or down. All API operations that require database access will fail. Users will experience errors on virtually all application functionality including authentication, data retrieval, and writes.

## Investigation Steps
1. Check the RDS instance status in the AWS Console or via CLI: `aws rds describe-db-instances --db-instance-identifier selfpublisherforge-production-postgres`. Look for the `DBInstanceStatus` field.
2. Review RDS event logs for recent events (failover, maintenance, storage full, reboot): `aws rds describe-events --source-identifier selfpublisherforge-production-postgres --source-type db-instance --duration 60`.
3. Verify network connectivity from the ECS tasks to the RDS instance. Check security groups, NACLs, and VPC routing tables to ensure the database port (5432) is accessible.
4. Check RDS CloudWatch metrics for CPU, memory, storage, and connection counts to identify resource exhaustion.
5. Attempt a manual connection test from a bastion host or a debug container in the same VPC.

## Resolution
### Common Causes
- **RDS instance stopped or rebooting**: If stopped, start the instance. If rebooting, wait for it to become available. Check if automated maintenance was scheduled.
- **Storage full**: If the RDS instance ran out of storage, it may become read-only or unresponsive. Increase allocated storage via `aws rds modify-db-instance --db-instance-identifier selfpublisherforge-production-postgres --allocated-storage <new-size> --apply-immediately`.
- **Security group misconfiguration**: Verify that the RDS security group allows inbound TCP on port 5432 from the ECS task security group. A recent infrastructure change may have modified rules.
- **RDS instance failover**: If Multi-AZ is enabled, a failover may have occurred. The application should reconnect automatically, but check that the DNS endpoint resolved correctly.
- **Parameter group change requiring restart**: Some RDS parameter changes require a reboot. Check if a pending reboot is needed.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Enable Multi-AZ deployments for automatic failover.
- Configure storage auto-scaling on the RDS instance.
- Set up RDS event subscriptions to notify on maintenance windows and instance state changes.
- Use connection pooling (e.g., PgBouncer) to manage connections and handle brief connectivity interruptions gracefully.
- Monitor free storage and connection counts with P2/P3 alerts to catch issues before they become critical.

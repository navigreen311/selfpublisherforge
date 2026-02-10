# Runbook Index

Operational runbooks for SelfPublisherForge production alerts. Each runbook corresponds to a Prometheus alert defined in [`infra/monitoring/alerts.yml`](../../infra/monitoring/alerts.yml).

## P0 - Critical (Immediate Response)

| Alert | Runbook | Service |
|-------|---------|---------|
| APIServiceDown | [api-service-down.md](api-service-down.md) | API |
| DatabaseConnectionFailure | [rds-connection-failure.md](rds-connection-failure.md) | Database |
| APIErrorRateCritical | [high-error-rate.md](high-error-rate.md) | API |
| RDSStorageSpaceCritical | [rds-storage-critical.md](rds-storage-critical.md) | Database |

## P1 - Urgent (Respond Within 15 Minutes)

| Alert | Runbook | Service |
|-------|---------|---------|
| APILatencyP95Critical | [high-latency.md](high-latency.md) | API |
| APIErrorRateWarning | [elevated-error-rate.md](elevated-error-rate.md) | API |
| CeleryQueueDepthCritical | [celery-queue-backup.md](celery-queue-backup.md) | Worker |
| RDSCPUCritical | [rds-high-cpu.md](rds-high-cpu.md) | Database |
| RedisMemoryUsageCritical | [redis-high-memory.md](redis-high-memory.md) | Redis |
| ElasticsearchClusterHealthRed | [elasticsearch-red.md](elasticsearch-red.md) | Elasticsearch |

## P2 - Warning (Respond Within 1 Hour)

| Alert | Runbook | Service |
|-------|---------|---------|
| ECSTaskRestarts | [ecs-task-restarts.md](ecs-task-restarts.md) | ECS |
| APILatencyP95Warning | [latency-investigation.md](latency-investigation.md) | API |
| CeleryTaskFailureRate | [celery-failures.md](celery-failures.md) | Worker |
| RDSFreeStorageLow | [rds-storage-low.md](rds-storage-low.md) | Database |
| DBConnectionPoolNearCapacity | [db-connection-pool.md](db-connection-pool.md) | Database |
| ElasticsearchClusterHealthYellow | [elasticsearch-yellow.md](elasticsearch-yellow.md) | Elasticsearch |

## P3 - Informational (Next Business Day)

| Alert | Runbook | Service |
|-------|---------|---------|
| HighCPUUsageSustained | [high-cpu.md](high-cpu.md) | ECS |
| RedisCacheHitRateLow | [redis-low-hit-rate.md](redis-low-hit-rate.md) | Redis |
| CeleryQueueGrowingTrend | [celery-queue-growing.md](celery-queue-growing.md) | Worker |
| DeploymentCompleted | [deployment-completed.md](deployment-completed.md) | Deploy |

## Escalation Policy

- **P0**: Page on-call engineer immediately. All hands on deck.
- **P1**: Page on-call engineer immediately. Respond within 15 minutes.
- **P2**: Create ticket, address within 4 hours.
- **P3**: Create ticket, address within 24 hours (next business day).

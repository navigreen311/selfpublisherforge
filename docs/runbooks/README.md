# SelfPublisherForge Runbooks

Operational runbooks for responding to production alerts defined in [`infra/monitoring/alerts.yml`](../../infra/monitoring/alerts.yml). Each runbook provides structured guidance for investigating and resolving specific alert conditions.

## How to Use This Guide

1. **Receive an alert** via PagerDuty, Slack (`#incidents`), or email.
2. **Find the matching runbook** in the index below using the alert name.
3. **Follow the Investigation steps** to identify the root cause.
4. **Apply the Resolution steps** to restore service.
5. **Escalate** per the runbook's escalation table if the issue is not resolving within the expected timeframe.
6. **Communicate** status updates in `#incidents` every 15 minutes during active incidents.
7. **Post-incident**: Create a review document for any P0 or P1 incident.

## Severity Tiers

| Tier | Response Time       | Action                                        |
|------|---------------------|-----------------------------------------------|
| P0   | Immediate (page)    | Service down or data loss risk. All hands.    |
| P1   | Within 15 minutes   | Degraded experience. Page on-call engineer.   |
| P2   | Within 1 hour       | Potential issue developing. Create ticket.     |
| P3   | Next business day   | Informational, trend tracking. Create ticket.  |

## Runbook Index

### P0 -- Critical (Immediate Response)

| Alert | Runbook | Service | Description |
|-------|---------|---------|-------------|
| `APIServiceDown` | [api-service-down.md](api-service-down.md) | API | API service has zero running tasks. Complete outage. |
| `DatabaseConnectionFailure` | [database-connection-issues.md](database-connection-issues.md) | Database | PostgreSQL is unreachable. All DB operations fail. |
| `APIErrorRateCritical` | [high-error-rate.md](high-error-rate.md) | API | 5xx error rate exceeds 5%. Widespread request failures. |
| `RDSStorageSpaceCritical` | [rds-storage-critical.md](rds-storage-critical.md) | Database | RDS free storage below 2 GB. Writes may fail. |

### P1 -- Urgent (Respond Within 15 Minutes)

| Alert | Runbook | Service | Description |
|-------|---------|---------|-------------|
| `APILatencyP95Critical` | [high-latency.md](high-latency.md) | API | P95 latency exceeds 2 seconds. Severe slowness. |
| `APIErrorRateWarning` | [high-error-rate.md](high-error-rate.md) / [elevated-error-rate.md](elevated-error-rate.md) | API | 5xx error rate exceeds 1% SLO. Error budget burning. |
| `CeleryQueueDepthCritical` | [celery-queue-depth.md](celery-queue-depth.md) | Worker | Queue exceeds 500 tasks. Background processing backed up. |
| `RDSCPUCritical` | [rds-high-cpu.md](rds-high-cpu.md) | Database | RDS CPU above 90%. Database performance degraded. |
| `RedisMemoryUsageCritical` | [high-memory-usage.md](high-memory-usage.md) | Redis | Redis memory above 90%. Cache evictions accelerating. |
| `ElasticsearchClusterHealthRed` | [elasticsearch-red.md](elasticsearch-red.md) | Elasticsearch | Cluster health RED. Search may be unavailable. |
| *(Proactive)* | [ssl-certificate-expiry.md](ssl-certificate-expiry.md) | Infrastructure | SSL cert expiring within 7 days. HTTPS will break. |

### P2 -- Warning (Respond Within 1 Hour)

| Alert | Runbook | Service | Description |
|-------|---------|---------|-------------|
| `APIServiceFlapping` | [ecs-task-restarts.md](ecs-task-restarts.md) | ECS | API changing state excessively. Possible crash loop. |
| `APILatencyP95Warning` | [latency-investigation.md](latency-investigation.md) | API | P95 latency exceeds 500ms SLO target. |
| `CeleryTaskFailureRate` | [celery-queue-depth.md](celery-queue-depth.md) / [celery-failures.md](celery-failures.md) | Worker | Task failure rate exceeds 5%. |
| `RDSFreeStorageLow` | [rds-storage-low.md](rds-storage-low.md) | Database | RDS free storage below 10 GB. Plan expansion. |
| `DBConnectionPoolNearCapacity` | [database-connection-issues.md](database-connection-issues.md) | Database | Connections above 150/200. Exhaustion imminent. |
| `ElasticsearchClusterHealthYellow` | [elasticsearch-yellow.md](elasticsearch-yellow.md) | Elasticsearch | Cluster health YELLOW. Redundancy reduced. |
| *(Proactive)* | [ssl-certificate-expiry.md](ssl-certificate-expiry.md) | Infrastructure | SSL cert expiring within 30 days. |

### P3 -- Informational (Next Business Day)

| Alert | Runbook | Service | Description |
|-------|---------|---------|-------------|
| `HighCPUUsageSustained` | [high-memory-usage.md](high-memory-usage.md) / [high-cpu.md](high-cpu.md) | ECS | CPU sustained above 70% for 1 hour. |
| `RedisCacheHitRateLow` | [redis-low-hit-rate.md](redis-low-hit-rate.md) | Redis | Cache hit rate below 80%. Review TTLs. |
| `CeleryQueueGrowingTrend` | [celery-queue-depth.md](celery-queue-depth.md) | Worker | Queue sustained above 100 for 1 hour. |
| `DeploymentCompleted` | [deployment-completed.md](deployment-completed.md) | Deploy | New production deployment detected. |

### Meta -- Monitoring Health

| Alert | Runbook | Service | Description |
|-------|---------|---------|-------------|
| `TargetDown` | [target-down.md](target-down.md) | Monitoring | Prometheus scrape target unreachable for 5 minutes. |
| `Watchdog` | [watchdog.md](watchdog.md) | Monitoring | Dead-man's switch. If this stops, alerting is broken. |

## Cross-Reference Guide

Some issues span multiple runbooks. Use this guide when your alert leads to a different root cause:

| Symptom | Start With | May Lead To |
|---------|-----------|-------------|
| API returning 500s | [high-error-rate.md](high-error-rate.md) | [database-connection-issues.md](database-connection-issues.md), [high-memory-usage.md](high-memory-usage.md) |
| API completely down | [api-service-down.md](api-service-down.md) | [high-memory-usage.md](high-memory-usage.md) (OOM), [ssl-certificate-expiry.md](ssl-certificate-expiry.md) |
| Background jobs stuck | [celery-queue-depth.md](celery-queue-depth.md) | [database-connection-issues.md](database-connection-issues.md), [high-memory-usage.md](high-memory-usage.md) (Redis) |
| Slow responses | [high-latency.md](high-latency.md) | [database-connection-issues.md](database-connection-issues.md), [high-memory-usage.md](high-memory-usage.md) |
| Redis memory full | [high-memory-usage.md](high-memory-usage.md) | [celery-queue-depth.md](celery-queue-depth.md) |

## Useful Links

| Resource | URL |
|----------|-----|
| Prometheus | `http://prometheus:9090` |
| Grafana Dashboards | `https://grafana.selfpublisherforge.com` |
| Flower (Celery Monitor) | `https://flower.selfpublisherforge.com` |
| AWS Console -- ECS | `https://console.aws.amazon.com/ecs` |
| AWS Console -- RDS | `https://console.aws.amazon.com/rds` |
| AWS Console -- ElastiCache | `https://console.aws.amazon.com/elasticache` |
| AWS Console -- ACM | `https://console.aws.amazon.com/acm` |
| Status Page | `https://status.selfpublisherforge.com` |
| PagerDuty | `https://selfpublisherforge.pagerduty.com` |
| Alert Rules Source | [`infra/monitoring/alerts.yml`](../../infra/monitoring/alerts.yml) |

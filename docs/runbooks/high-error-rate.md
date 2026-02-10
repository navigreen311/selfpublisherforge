# Runbook: High Error Rate

## Alert

| Field       | Value                                                                                                                       |
|-------------|-----------------------------------------------------------------------------------------------------------------------------|
| Alert Name  | `APIErrorRateCritical` (P0) / `APIErrorRateWarning` (P1)                                                                   |
| Expression  | `(sum(rate(http_requests_total{job="spf-api", status=~"5.."}[5m])) / sum(rate(http_requests_total{job="spf-api"}[5m]))) * 100 > 5` (P0, 5m) or `> 1` (P1, 10m) |
| Severity    | **P0 -- Critical** (>5% error rate) / **P1 -- Urgent** (>1% SLO breach)                                                    |
| Service     | `api`                                                                                                                       |
| Environment | `production`                                                                                                                |
| Runbook URL | `docs/runbooks/high-error-rate.md` (P0) / `docs/runbooks/elevated-error-rate.md` (P1)                                      |

The P0 alert fires when more than 5% of API requests return HTTP 5xx status codes over a 5-minute window, sustained for 5 minutes. The P1 alert fires at the 1% SLO threshold over a 10-minute window, sustained for 10 minutes.

## Impact

- **P0 (>5%)**: A significant portion of user requests are failing. Core functionality (book creation, publishing, account management) is broken for many users.
- **P1 (>1%)**: The error rate SLO is breached. Error budget is being consumed. Some users are experiencing intermittent failures.
- Third-party integrations and webhooks may start retrying failed requests, amplifying load.
- Revenue impact: failed checkout flows, lost publishing submissions.

## Investigation

### 1. Confirm error rate and identify scope

```bash
# Query Prometheus for current error rate percentage
curl -s 'http://prometheus:9090/api/v1/query?query=\
(sum(rate(http_requests_total{job="spf-api",status=~"5.."}[5m]))\
/sum(rate(http_requests_total{job="spf-api"}[5m])))*100'

# Break down errors by endpoint, method, and status code (top 10)
curl -s 'http://prometheus:9090/api/v1/query?query=\
topk(10,sum(rate(http_requests_total{job="spf-api",status=~"5.."}[5m]))\
by(handler,method,status))'

# Check if errors are concentrated on specific status codes
curl -s 'http://prometheus:9090/api/v1/query?query=\
sum(rate(http_requests_total{job="spf-api",status=~"5.."}[5m]))by(status)'
```

### 2. Check recent deployments

```bash
# List recent deployments and their timestamps
aws ecs describe-services \
  --cluster selfpublisherforge-production \
  --services spf-api \
  --query 'services[0].deployments[].{
    id: id,
    status: status,
    taskDefinition: taskDefinition,
    createdAt: createdAt,
    runningCount: runningCount
  }'

# Check recent service events for deployment activity
aws ecs describe-services \
  --cluster selfpublisherforge-production \
  --services spf-api \
  --query 'services[0].events[:10].{at:createdAt,msg:message}'
```

### 3. Analyze application logs

```bash
# Tail recent error logs
aws logs tail /ecs/selfpublisherforge-production/spf-api \
  --since 15m \
  --format short \
  --filter-pattern '"ERROR" OR "500" OR "Traceback" OR "Exception"'

# Find the most common exception types
aws logs filter-log-events \
  --log-group-name /ecs/selfpublisherforge-production/spf-api \
  --start-time $(date -d '30 minutes ago' +%s000) \
  --filter-pattern '"Traceback"' \
  --query 'events[].message' \
  --limit 20

# Look for specific HTTP 502/503/504 patterns
aws logs filter-log-events \
  --log-group-name /ecs/selfpublisherforge-production/spf-api \
  --start-time $(date -d '30 minutes ago' +%s000) \
  --filter-pattern '"status_code=50"' \
  --query 'events[].message' \
  --limit 20
```

### 4. Check downstream dependencies

```bash
# Database: check RDS instance status
aws rds describe-db-instances \
  --db-instance-identifier selfpublisherforge-production-postgres \
  --query 'DBInstances[0].{Status:DBInstanceStatus,CPU:PerformanceInsightsEnabled}'

# Database: check connection count via Prometheus
curl -s 'http://prometheus:9090/api/v1/query?query=\
pg_stat_activity_count{instance=~"selfpublisherforge-production-postgres.*"}'

# Redis: check connectivity
redis-cli -h <redis-endpoint> -p 6379 ping

# Redis: check memory pressure
redis-cli -h <redis-endpoint> -p 6379 INFO memory | grep used_memory_human

# Elasticsearch: check cluster health
curl -s http://<elasticsearch-endpoint>:9200/_cluster/health?pretty
```

### 5. Check resource saturation

```bash
# ECS API service CPU utilization (last 30 minutes)
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=spf-api Name=ClusterName,Value=selfpublisherforge-production \
  --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum

# ECS API service memory utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ServiceName,Value=spf-api Name=ClusterName,Value=selfpublisherforge-production \
  --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum
```

## Resolution

### Errors caused by a bad deployment

1. Identify the previous working task definition:
   ```bash
   aws ecs list-task-definitions \
     --family-prefix spf-api \
     --sort DESC \
     --query 'taskDefinitionArns[:3]'
   ```

2. Roll back to the previous revision:
   ```bash
   aws ecs update-service \
     --cluster selfpublisherforge-production \
     --service spf-api \
     --task-definition spf-api:<previous-revision-number>
   ```

3. Monitor error rate for 5 minutes to confirm recovery:
   ```bash
   watch -n 30 'curl -s "http://prometheus:9090/api/v1/query?query=\
   (sum(rate(http_requests_total{job=\"spf-api\",status=~\"5..\"}[5m]))\
   /sum(rate(http_requests_total{job=\"spf-api\"}[5m])))*100" \
   | python3 -c "import sys,json; print(json.load(sys.stdin)[\"data\"][\"result\"][0][\"value\"][1])"'
   ```

4. Notify the deploying engineer with the relevant error logs.

### Errors caused by a downstream dependency failure

- **Database failure**: See [database-connection-issues.md](database-connection-issues.md).
- **Redis failure**: Restart API tasks to reset Redis connections, or check Redis instance status.
- **Elasticsearch failure**: Check cluster health. If RED, see the `elasticsearch-red.md` runbook.
- **External API outage** (Stripe, etc.): Check the vendor's status page. Enable circuit breakers if available. Consider feature flags to disable dependent features.

### Errors caused by resource exhaustion

1. Scale out the API service:
   ```bash
   # Get current count
   CURRENT=$(aws ecs describe-services \
     --cluster selfpublisherforge-production \
     --services spf-api \
     --query 'services[0].desiredCount' --output text)

   # Scale up by 2
   aws ecs update-service \
     --cluster selfpublisherforge-production \
     --service spf-api \
     --desired-count $((CURRENT + 2))
   ```

2. If database connections are saturated, see [database-connection-issues.md](database-connection-issues.md).

### Errors caused by a specific endpoint or request pattern

1. Identify the endpoint from step 1 above.
2. Check if a specific user, IP, or integration is sending problematic requests.
3. If needed, temporarily block the traffic at the WAF or ALB level:
   ```bash
   # Example: add a WAF rule to rate-limit a specific path
   # This is situation-specific -- coordinate with the infrastructure team
   ```

## Escalation

| Condition                                           | Escalate To                       |
|-----------------------------------------------------|-----------------------------------|
| Error rate >5% and no obvious cause within 10 min   | Engineering Lead                  |
| Root cause is a bad deployment, deployer unknown     | On-call Engineering Lead          |
| Downstream dependency outage (AWS, Stripe, etc.)    | Relevant service owner            |
| Error rate not decreasing after rollback             | VP Engineering                    |
| Customer-visible impact exceeding 15 minutes         | VP Engineering + CTO              |

### Communication

- Post in `#incidents` with the current error rate and the affected endpoints.
- If customer-facing, update the status page at https://status.selfpublisherforge.com.
- For P0: open a bridge call if not resolved within 10 minutes.
- After resolution, create a post-incident review document.

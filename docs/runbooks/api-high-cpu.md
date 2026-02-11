# Runbook: API High CPU

## Alert

| Field       | Value                                                      |
|-------------|------------------------------------------------------------|
| Alert Name  | `APIProcessCPUHigh`                                        |
| Expression  | `rate(process_cpu_seconds_total{job="spf-api"}[5m]) > 0.9` for 10 minutes |
| Severity    | **P1 -- Urgent**                                           |
| Service     | `api`                                                      |
| Environment | `production`                                               |
| Runbook URL | `docs/runbooks/api-high-cpu.md`                            |

Fires when the SelfPublisherForge API process CPU usage is sustained above 90% of a CPU core for more than 10 minutes. The `rate(process_cpu_seconds_total[5m])` metric gives the fraction of a CPU core consumed per second (1.0 = 100% of one core).

## Severity

**P1 -- Urgent. Respond within 15 minutes.** Sustained high CPU usage on the API service indicates performance degradation. Users are likely experiencing slow response times, timeouts, or errors. If left unaddressed, the service may become unresponsive.

## Symptoms

- API response times are elevated (check the `APILatencyP95Critical` and `APILatencyP95Warning` alerts).
- Users report slowness or timeouts when using the application.
- Prometheus shows `rate(process_cpu_seconds_total{job="spf-api"}[5m])` above 0.9.
- The API process is consuming most or all of its allocated CPU resources.
- Other metrics from the API service (request rate, error rate) may be affected.

## Investigation Steps

### 1. Confirm current CPU usage

```bash
# Check the current CPU rate from Prometheus
curl -sS 'http://localhost:9090/api/v1/query?query=rate(process_cpu_seconds_total{job="spf-api"}[5m])' | \
  jq '.data.result[].value[1]'

# Check container-level CPU usage
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
  $(docker ps --filter "name=spf-api" -q)
```

### 2. Check for traffic spikes

```bash
# Query the current request rate
curl -sS 'http://localhost:9090/api/v1/query?query=sum(rate(http_requests_total{job="spf-api"}[5m]))' | \
  jq '.data.result[].value[1]'

# Compare against the rate from 1 hour ago
curl -sS 'http://localhost:9090/api/v1/query?query=sum(rate(http_requests_total{job="spf-api"}[5m] offset 1h))' | \
  jq '.data.result[].value[1]'

# Check request rate by endpoint to find hot paths
curl -sS 'http://localhost:9090/api/v1/query?query=topk(10, sum by (handler, method) (rate(http_requests_total{job="spf-api"}[5m])))' | \
  jq '.data.result[] | {endpoint: .metric.handler, method: .metric.method, rate: .value[1]}'
```

### 3. Identify expensive queries or endpoints

```bash
# Check the slowest endpoints by P95 latency
curl -sS 'http://localhost:9090/api/v1/query?query=topk(10, histogram_quantile(0.95, sum by (handler, le) (rate(http_request_duration_seconds_bucket{job="spf-api"}[5m]))))' | \
  jq '.data.result[] | {endpoint: .metric.handler, p95_seconds: .value[1]}'

# Check application logs for slow queries or warnings
aws logs filter-log-events \
  --log-group-name /ecs/selfpublisherforge-production/spf-api \
  --start-time $(date -d '30 minutes ago' +%s000) \
  --filter-pattern '"slow query" OR "timeout" OR "WARNING"' \
  --query 'events[].message' \
  --limit 20
```

### 4. Check for memory leaks or garbage collection pressure

```bash
# Check process memory usage (high GC pressure can cause CPU spikes)
curl -sS 'http://localhost:9090/api/v1/query?query=process_resident_memory_bytes{job="spf-api"}' | \
  jq '.data.result[].value[1]'

# Check if memory has been growing over time
curl -sS 'http://localhost:9090/api/v1/query_range?query=process_resident_memory_bytes{job="spf-api"}&start='$(date -d '6 hours ago' +%s)'&end='$(date +%s)'&step=300' | \
  jq '.data.result[].values | last'
```

### 5. Check for recent deployments

```bash
# List recent deployments
aws ecs describe-services \
  --cluster selfpublisherforge-production \
  --services spf-api \
  --query 'services[0].deployments[].{
    id: id,
    status: status,
    taskDefinition: taskDefinition,
    desiredCount: desiredCount,
    runningCount: runningCount,
    createdAt: createdAt
  }'

# Check recent code changes that may have introduced CPU-intensive operations
aws ecs describe-task-definition \
  --task-definition spf-api \
  --query 'taskDefinition.containerDefinitions[0].image'
```

### 6. Check database query performance

```bash
# Check for long-running queries on PostgreSQL
# (requires access to the database)
psql -h <db-host> -U <db-user> -d selfpublisherforge -c "
  SELECT pid, now() - pg_stat_activity.query_start AS duration,
         query, state
  FROM pg_stat_activity
  WHERE state != 'idle'
    AND now() - pg_stat_activity.query_start > interval '5 seconds'
  ORDER BY duration DESC
  LIMIT 10;"
```

## Resolution

### Traffic spike

1. Scale out the API service to handle the increased load:
   ```bash
   aws ecs update-service \
     --cluster selfpublisherforge-production \
     --service spf-api \
     --desired-count <current-count + N>
   ```
2. If the traffic spike is from a specific source (bot, DDoS), implement rate limiting or block the source at the ALB/WAF level.

### Expensive query or endpoint

1. Identify the problematic endpoint from the investigation steps above.
2. Add database query optimization (indexes, query rewriting) for slow queries.
3. Add caching for expensive computations or frequently accessed data.
4. If an endpoint is performing unnecessary work, deploy a hotfix.

### Memory leak causing GC pressure

1. If memory is growing continuously, a memory leak is likely causing excessive garbage collection, which consumes CPU.
2. See [high-memory.md](high-memory.md) for memory-specific investigation.
3. As an immediate mitigation, restart the API service:
   ```bash
   aws ecs update-service \
     --cluster selfpublisherforge-production \
     --service spf-api \
     --force-new-deployment
   ```

### Bad deployment

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

### Insufficient CPU allocation

1. Review the current task definition CPU allocation:
   ```bash
   aws ecs describe-task-definition \
     --task-definition spf-api \
     --query 'taskDefinition.{cpu: cpu, memory: memory}'
   ```
2. If the service has outgrown its allocation, increase the CPU units in the task definition and redeploy.

## Escalation

| Condition                                                 | Escalate To                      |
|-----------------------------------------------------------|----------------------------------|
| CPU remains above 90% after scaling and restart           | Engineering Lead                 |
| Root cause is a code regression                           | Deploying engineer               |
| Users are experiencing errors or timeouts                 | Engineering Lead + on-call       |
| Database is the bottleneck                                | Database Lead                    |
| Suspected DDoS or abusive traffic                         | Infrastructure / Security team   |

### Communication

- Post a status update in `#incidents` Slack channel if users are experiencing degraded performance.
- If P95 latency alerts are also firing, coordinate response across both alerts.
- After resolution, monitor CPU for at least 30 minutes to confirm the fix is stable.

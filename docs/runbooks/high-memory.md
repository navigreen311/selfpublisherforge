# Runbook: High Memory

## Alert

| Field       | Value                                                      |
|-------------|------------------------------------------------------------|
| Alert Name  | `APIProcessMemoryHigh`                                     |
| Expression  | `process_resident_memory_bytes{job="spf-api"} > 536870912` for 1 hour |
| Severity    | **P3 -- Informational**                                    |
| Service     | `api`                                                      |
| Environment | `production`                                               |
| Runbook URL | `docs/runbooks/high-memory.md`                             |

Fires when the SelfPublisherForge API process resident memory (RSS) has been sustained above 512 MB for 1 hour. This may indicate a memory leak, undersized memory allocation, or a need for scaling review.

## Severity

**P3 -- Informational. Respond next business day.** The service is still functioning, but memory usage is elevated. If left unaddressed, continued memory growth could lead to OOM kills, service restarts, and eventual P0/P1 incidents.

## Symptoms

- Prometheus shows `process_resident_memory_bytes{job="spf-api"}` above 536870912 (512 MB).
- Memory usage may be trending upward over hours or days (indicates a memory leak).
- The API service may exhibit increased garbage collection pauses, causing intermittent latency spikes.
- In severe cases, the container may be OOM-killed by the kernel or Docker runtime, triggering the `APIServiceDown` or `APIServiceFlapping` alerts.
- CloudWatch or Docker stats show the container approaching its memory limit.

## Investigation Steps

### 1. Confirm current memory usage

```bash
# Check current process memory from Prometheus
curl -sS 'http://localhost:9090/api/v1/query?query=process_resident_memory_bytes{job="spf-api"}' | \
  jq '.data.result[].value[1]'

# Check container-level memory usage and limits
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}" \
  $(docker ps --filter "name=spf-api" -q)
```

### 2. Check memory growth trend

```bash
# Query memory usage over the last 24 hours (5-minute intervals)
curl -sS 'http://localhost:9090/api/v1/query_range?query=process_resident_memory_bytes{job="spf-api"}&start='$(date -d '24 hours ago' +%s)'&end='$(date +%s)'&step=300' | \
  jq '.data.result[].values | [first, last] | map({time: .[0], bytes: .[1]})'

# Check if memory increases linearly over time (leak indicator)
# A steadily increasing line with no drops suggests a memory leak.
# Periodic drops followed by regrowth suggest GC is reclaiming memory normally.
```

### 3. Check the task definition memory limits

```bash
# Check the allocated memory for the API task
aws ecs describe-task-definition \
  --task-definition spf-api \
  --query 'taskDefinition.containerDefinitions[0].{
    memory: memory,
    memoryReservation: memoryReservation,
    cpu: cpu
  }'
```

### 4. Investigate potential memory leaks

```bash
# Check application logs for memory-related warnings
aws logs filter-log-events \
  --log-group-name /ecs/selfpublisherforge-production/spf-api \
  --start-time $(date -d '6 hours ago' +%s000) \
  --filter-pattern '"memory" OR "MemoryError" OR "OOMKilled" OR "gc" OR "heap"' \
  --query 'events[].message' \
  --limit 30

# Check for large response payloads or data processing
aws logs filter-log-events \
  --log-group-name /ecs/selfpublisherforge-production/spf-api \
  --start-time $(date -d '1 hour ago' +%s000) \
  --filter-pattern '"large" OR "payload" OR "bulk" OR "export"' \
  --query 'events[].message' \
  --limit 20
```

### 5. Check for correlation with traffic or specific endpoints

```bash
# Check current request rate
curl -sS 'http://localhost:9090/api/v1/query?query=sum(rate(http_requests_total{job="spf-api"}[5m]))' | \
  jq '.data.result[].value[1]'

# Check if specific endpoints are handling large data volumes
curl -sS 'http://localhost:9090/api/v1/query?query=topk(10, sum by (handler) (rate(http_requests_total{job="spf-api"}[1h])))' | \
  jq '.data.result[] | {endpoint: .metric.handler, rate: .value[1]}'
```

### 6. Check recent deployments

```bash
# Check if a recent deployment correlates with the memory increase
aws ecs describe-services \
  --cluster selfpublisherforge-production \
  --services spf-api \
  --query 'services[0].deployments[].{
    id: id,
    status: status,
    taskDefinition: taskDefinition,
    createdAt: createdAt
  }'
```

## Resolution

### Memory leak confirmed (steadily increasing memory with no recovery)

1. Identify the source of the leak by reviewing recent code changes, especially:
   - Global caches or dictionaries that grow without bounds.
   - Event listeners or callbacks that are registered but never removed.
   - Database connections or file handles that are opened but never closed.
   - Large objects held in request-scoped variables that outlive the request.

2. As an immediate mitigation, restart the API service to reclaim memory:
   ```bash
   aws ecs update-service \
     --cluster selfpublisherforge-production \
     --service spf-api \
     --force-new-deployment
   ```

3. If the leak is severe and recurs quickly, set up a periodic restart schedule while the fix is being developed.

### Legitimate memory growth (traffic increase or new features)

1. Increase the memory allocation in the ECS task definition:
   ```bash
   # Create a new task definition revision with increased memory
   # Update the memory and memoryReservation values as needed
   aws ecs describe-task-definition --task-definition spf-api \
     --query 'taskDefinition' > /tmp/task-def.json
   # Edit /tmp/task-def.json to increase memory values
   # Register the new task definition and update the service
   ```

2. Scale out the service to distribute memory load across more tasks:
   ```bash
   aws ecs update-service \
     --cluster selfpublisherforge-production \
     --service spf-api \
     --desired-count <current-count + N>
   ```

### Large data processing operations

1. If specific endpoints are loading large datasets into memory (e.g., bulk exports, report generation), refactor to use streaming or pagination.
2. Move heavy data processing to background Celery workers rather than handling in the API process.
3. Add per-request memory limits or timeouts for data-intensive operations.

### Caching issues

1. Review in-process caches (e.g., Django cache framework with local memory backend) for unbounded growth.
2. Set maximum cache sizes and TTLs on all in-memory caches.
3. Consider moving caches to Redis to avoid consuming API process memory.

## Escalation

| Condition                                                   | Escalate To                      |
|-------------------------------------------------------------|----------------------------------|
| Memory is approaching the container limit (risk of OOM)     | On-call engineer (treat as P1)   |
| Memory leak confirmed but root cause unknown                | Engineering Lead                 |
| Service is OOM-killed repeatedly                            | Engineering Lead (follow [api-service-down.md](api-service-down.md)) |
| Memory growth correlates with a recent deployment           | Deploying engineer               |
| Requires infrastructure changes (task definition, scaling)  | DevOps / Infrastructure team     |

### Communication

- For P3 severity, create a ticket for next-business-day review.
- If memory usage is approaching the container limit and OOM kills are imminent, escalate to P1 and post in `#incidents` Slack channel.
- Track memory trends over multiple days to establish baseline usage patterns.
- After resolution, monitor memory for at least 48 hours to confirm the fix is effective.

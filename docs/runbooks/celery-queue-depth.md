# Runbook: Celery Queue Depth

## Alert

| Field       | Value                                                                                             |
|-------------|---------------------------------------------------------------------------------------------------|
| Alert Name  | `CeleryQueueDepthCritical` (P1) / `CeleryQueueGrowingTrend` (P3)                                 |
| Expression  | `celery_queue_length{queue="celery", env="production"} > 500` for 10m (P1) or `> 100` for 1h (P3)|
| Severity    | **P1 -- Urgent** (>500 tasks for 10m) / **P3 -- Informational** (>100 sustained for 1h)          |
| Service     | `worker`                                                                                          |
| Environment | `production`                                                                                      |
| Runbook URL | `docs/runbooks/celery-queue-backup.md` (P1) / `docs/runbooks/celery-queue-growing.md` (P3)        |

Metrics are exported by celery-exporter (danihodovic/celery-exporter), scraped via the `spf-celery-exporter` job on `celery-exporter:9808`.

Related alert: `CeleryTaskFailureRate` (P2) fires when the task failure rate exceeds 5%. See the "Task failures contributing to backup" section below.

## Impact

- **Background job processing is delayed.** Tasks such as book generation, PDF rendering, email delivery, and webhook processing accumulate in the queue without timely processing.
- Users see "processing" states that never resolve (e.g., "Your book is being generated" stays pending indefinitely).
- If the queue grows unbounded, Redis broker memory may be exhausted, risking loss of queued tasks.
- Tasks with `expires` or `time_limit` settings may expire before being executed, causing silent failures.
- Downstream systems expecting webhook callbacks or email notifications will not receive them.

## Investigation

### 1. Check current queue depth and trend

```bash
# Query Prometheus for current queue length
curl -s 'http://prometheus:9090/api/v1/query?query=\
celery_queue_length{queue="celery",env="production"}'

# Check queue depth trend over the last 2 hours
curl -s 'http://prometheus:9090/api/v1/query_range?query=\
celery_queue_length{queue="celery",env="production"}\
&start='"$(date -u -d '2 hours ago' +%Y-%m-%dT%H:%M:%S)"'Z\
&end='"$(date -u +%Y-%m-%dT%H:%M:%S)"'Z&step=5m'

# Check queue length directly in Redis
redis-cli -h <redis-endpoint> -p 6379 LLEN celery
```

### 2. Check worker status via Flower

```bash
# Flower dashboard URL (for visual inspection):
# https://flower.selfpublisherforge.com

# List active workers and their status via Flower API
curl -s https://flower.selfpublisherforge.com/api/workers | python3 -c "
import json, sys
workers = json.load(sys.stdin)
for name, info in workers.items():
    active = len(info.get('active', []))
    registered = len(info.get('registered', []))
    stats = info.get('stats', {})
    processed = stats.get('total', {})
    print(f'{name}:')
    print(f'  active_tasks={active}, registered_tasks={registered}')
    print(f'  concurrency={info.get(\"stats\", {}).get(\"pool\", {}).get(\"max-concurrency\", \"unknown\")}')
    print(f'  status={\"online\" if info.get(\"status\") else \"offline\"}')
"

# Check for tasks that are stuck in STARTED state
curl -s 'https://flower.selfpublisherforge.com/api/tasks?state=STARTED&limit=20' \
  | python3 -m json.tool
```

### 3. Check ECS worker task status

```bash
# List running worker tasks
aws ecs list-tasks \
  --cluster selfpublisherforge-production \
  --service-name spf-celery-worker \
  --desired-status RUNNING

# Describe the worker service (desired vs running, recent events)
aws ecs describe-services \
  --cluster selfpublisherforge-production \
  --services spf-celery-worker \
  --query 'services[0].{
    desiredCount: desiredCount,
    runningCount: runningCount,
    pendingCount: pendingCount,
    events: events[:5]
  }'

# Check for recently stopped worker tasks (crash loops)
STOPPED_TASKS=$(aws ecs list-tasks \
  --cluster selfpublisherforge-production \
  --service-name spf-celery-worker \
  --desired-status STOPPED \
  --query 'taskArns[:3]' --output text)

if [ -n "$STOPPED_TASKS" ]; then
  aws ecs describe-tasks \
    --cluster selfpublisherforge-production \
    --tasks $STOPPED_TASKS \
    --query 'tasks[].{
      taskArn: taskArn,
      stoppedReason: stoppedReason,
      stopCode: stopCode,
      stoppedAt: stoppedAt
    }'
fi
```

### 4. Check worker logs for errors

```bash
# Tail worker logs for recent errors
aws logs tail /ecs/selfpublisherforge-production/spf-celery-worker \
  --since 30m \
  --format short

# Search for task failures and exceptions
aws logs filter-log-events \
  --log-group-name /ecs/selfpublisherforge-production/spf-celery-worker \
  --start-time $(date -d '30 minutes ago' +%s000) \
  --filter-pattern '"Task failed" OR "Exception" OR "Traceback" OR "WorkerLostError" OR "TimeLimitExceeded"' \
  --query 'events[].message' \
  --limit 20
```

### 5. Identify what types of tasks are queued

```bash
# Task receive rate by task name (which tasks are being submitted most)
curl -s 'http://prometheus:9090/api/v1/query?query=\
topk(10,sum(rate(celery_task_received_total{env="production"}[10m]))by(name))'

# Task failure rate by task name (which tasks are failing most)
curl -s 'http://prometheus:9090/api/v1/query?query=\
topk(5,sum(rate(celery_task_failed_total{env="production"}[30m]))by(name))'

# Task success rate by task name
curl -s 'http://prometheus:9090/api/v1/query?query=\
topk(5,sum(rate(celery_task_succeeded_total{env="production"}[30m]))by(name))'
```

### 6. Check Redis broker health

```bash
# Check Redis memory usage
redis-cli -h <redis-endpoint> -p 6379 INFO memory | grep -E "used_memory_human|maxmemory_human"

# Check if Redis is rejecting connections
redis-cli -h <redis-endpoint> -p 6379 INFO stats | grep rejected_connections

# Check Redis connected clients
redis-cli -h <redis-endpoint> -p 6379 INFO clients | grep connected_clients
```

## Resolution

### Workers are down or insufficient

1. **Scale up worker count:**
   ```bash
   CURRENT=$(aws ecs describe-services \
     --cluster selfpublisherforge-production \
     --services spf-celery-worker \
     --query 'services[0].desiredCount' --output text)

   aws ecs update-service \
     --cluster selfpublisherforge-production \
     --service spf-celery-worker \
     --desired-count $((CURRENT + 2))
   ```

2. **Force new deployment** if workers are stuck or unhealthy:
   ```bash
   aws ecs update-service \
     --cluster selfpublisherforge-production \
     --service spf-celery-worker \
     --force-new-deployment
   ```

3. Monitor the queue depth for 5-10 minutes to confirm it is draining:
   ```bash
   watch -n 30 'redis-cli -h <redis-endpoint> -p 6379 LLEN celery'
   ```

### A specific task type is causing the backup

1. Identify the problematic task type from step 5 above.
2. Revoke a stuck individual task:
   ```bash
   # Via Flower API
   curl -X POST https://flower.selfpublisherforge.com/api/task/revoke/<task-id>

   # Via celery CLI (from within a worker container)
   celery -A selfpublisherforge control revoke <task-id> --terminate
   ```

3. If an entire task class is broken, consider disabling it via application configuration or environment variable until a fix is deployed.

### Queue needs to be purged

**WARNING: This deletes all pending tasks. Only use this if queued tasks are safe to discard (e.g., they will be re-triggered or are no longer relevant).**

```bash
# Purge via celery CLI (from within a worker container)
celery -A selfpublisherforge purge -f

# Or purge directly in Redis
redis-cli -h <redis-endpoint> -p 6379 DEL celery

# Verify the queue is empty
redis-cli -h <redis-endpoint> -p 6379 LLEN celery
```

### Task failures contributing to backup

If `CeleryTaskFailureRate` (P2) is also firing:

1. Check specific task errors in worker logs (step 4 above).
2. Common failure causes:
   - **Database connection failures**: See [database-connection-issues.md](database-connection-issues.md).
   - **External API timeouts**: Check the specific integration and consider increasing task timeouts or adding retries.
   - **Code bugs from a recent deployment**: Roll back the worker task definition:
     ```bash
     aws ecs list-task-definitions --family-prefix spf-celery-worker --sort DESC --query 'taskDefinitionArns[:3]'
     aws ecs update-service \
       --cluster selfpublisherforge-production \
       --service spf-celery-worker \
       --task-definition spf-celery-worker:<previous-revision>
     ```

### Redis memory pressure from queue growth

If the queue backup is causing Redis to approach its memory limit:
1. See [high-memory-usage.md](high-memory-usage.md) for Redis memory management.
2. Consider purging low-priority tasks to free memory.
3. Scale up Redis instance if this is a recurring problem.

## Escalation

| Condition                                            | Escalate To              |
|------------------------------------------------------|--------------------------|
| Workers are down and cannot be restarted              | Engineering Lead         |
| Queue depth growing despite sufficient workers        | Backend Engineering Lead |
| Redis memory exhaustion imminent from queue growth    | Infrastructure Lead      |
| Task failures caused by a bad deployment              | Deploying engineer       |
| Customer-visible delays exceeding 30 minutes          | Engineering Lead         |
| Queue purge required (data loss decision)             | Engineering Lead         |

### Communication

- Post in `#incidents` with the current queue depth, worker count, and processing rate.
- If user-visible features are delayed (book generation, email delivery), notify Customer Success.
- For P1: monitor queue depth every 5 minutes until it stabilizes below 100.
- After resolution, create a post-incident review if queue depth exceeded 1000 or lasted more than 1 hour.

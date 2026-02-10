# Runbook: High Memory Usage

## Alert

| Field       | Value                                                                                                  |
|-------------|--------------------------------------------------------------------------------------------------------|
| Alert Name  | `RedisMemoryUsageCritical` (P1) / `HighCPUUsageSustained` (P3, also relevant for container memory)     |
| Expression  | `(redis_used_memory_bytes / redis_config_maxmemory) * 100 > 90` for 10m (P1)                           |
| Severity    | **P1 -- Urgent** (Redis >90% memory) / **P3 -- Informational** (ECS sustained resource pressure)      |
| Service     | `redis` / `ecs`                                                                                        |
| Environment | `production`                                                                                           |
| Runbook URL | `docs/runbooks/redis-high-memory.md` (P1) / `docs/runbooks/high-cpu.md` (P3)                          |

This runbook covers high memory usage for both Redis (ElastiCache) and ECS container workloads. The primary P1 alert fires when Redis memory usage exceeds 90% of its configured `maxmemory`. ECS container memory issues typically manifest as OOM kills, which are covered in [api-service-down.md](api-service-down.md) for crash scenarios.

## Impact

### Redis memory critical (P1)
- LRU cache eviction accelerates, degrading cache hit rate and increasing database load.
- If `maxmemory` is reached with a `noeviction` policy, Redis rejects write commands. This causes Celery task submission failures and cache write errors.
- Application performance degrades as cache misses force more requests to hit the database.
- Celery broker operations may fail, preventing new background tasks from being queued.

### ECS container memory
- Containers approaching memory limits experience increased garbage collection pauses and higher response latency.
- Containers exceeding their hard memory limit are OOM-killed by the ECS agent, causing request failures and potential service disruption.
- Repeated OOM kills trigger the `APIServiceFlapping` (P2) alert.

## Investigation

### Redis Memory

#### 1. Check current Redis memory usage

```bash
# Get Redis memory statistics
redis-cli -h <redis-endpoint> -p 6379 INFO memory

# Key metrics to examine:
#   used_memory_human      -- Current memory usage
#   used_memory_peak_human -- Peak usage since last restart
#   maxmemory_human        -- Configured memory limit
#   maxmemory_policy       -- Eviction policy (should be allkeys-lru or volatile-lru)
#   mem_fragmentation_ratio -- Should be close to 1.0; >1.5 indicates fragmentation

# Query Prometheus for Redis memory trend over the last 6 hours
curl -s 'http://prometheus:9090/api/v1/query_range?query=\
(redis_used_memory_bytes{instance=~"selfpublisherforge-production-redis.*"}\
/redis_config_maxmemory{instance=~"selfpublisherforge-production-redis.*"})*100\
&start='"$(date -u -d '6 hours ago' +%Y-%m-%dT%H:%M:%S)"'Z\
&end='"$(date -u +%Y-%m-%dT%H:%M:%S)"'Z&step=5m'
```

#### 2. Identify what is consuming memory

```bash
# Get key count per database
redis-cli -h <redis-endpoint> -p 6379 INFO keyspace

# Scan for the largest keys (top memory consumers)
redis-cli -h <redis-endpoint> -p 6379 --bigkeys

# Check total key count
redis-cli -h <redis-endpoint> -p 6379 DBSIZE

# Check Celery queue sizes (queues are stored as Redis lists)
redis-cli -h <redis-endpoint> -p 6379 LLEN celery
redis-cli -h <redis-endpoint> -p 6379 LLEN celery-priority

# Check memory usage of a specific key
redis-cli -h <redis-endpoint> -p 6379 MEMORY USAGE <key-name>

# Scan for key patterns and their counts
redis-cli -h <redis-endpoint> -p 6379 --scan --pattern "cache:*" | wc -l
redis-cli -h <redis-endpoint> -p 6379 --scan --pattern "session:*" | wc -l
redis-cli -h <redis-endpoint> -p 6379 --scan --pattern "celery-task-meta-*" | wc -l
```

#### 3. Check eviction and hit rate

```bash
# Check eviction statistics
redis-cli -h <redis-endpoint> -p 6379 INFO stats | grep -E "evicted_keys|keyspace_hits|keyspace_misses|rejected_connections"

# Query Prometheus for cache hit rate
curl -s 'http://prometheus:9090/api/v1/query?query=\
(rate(redis_keyspace_hits_total{instance=~"selfpublisherforge-production-redis.*"}[5m])\
/(rate(redis_keyspace_hits_total{instance=~"selfpublisherforge-production-redis.*"}[5m])\
+rate(redis_keyspace_misses_total{instance=~"selfpublisherforge-production-redis.*"}[5m])))*100'
```

### ECS Container Memory

#### 1. Check container memory utilization

```bash
# API service memory utilization (last 1 hour)
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ServiceName,Value=spf-api Name=ClusterName,Value=selfpublisherforge-production \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum

# Worker service memory utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ServiceName,Value=spf-celery-worker Name=ClusterName,Value=selfpublisherforge-production \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum
```

#### 2. Check for OOM kills

```bash
# Check recently stopped tasks for OOM stop reasons
STOPPED_TASKS=$(aws ecs list-tasks \
  --cluster selfpublisherforge-production \
  --service-name spf-api \
  --desired-status STOPPED \
  --query 'taskArns[:5]' --output text)

if [ -n "$STOPPED_TASKS" ]; then
  aws ecs describe-tasks \
    --cluster selfpublisherforge-production \
    --tasks $STOPPED_TASKS \
    --query 'tasks[].{
      taskArn: taskArn,
      stoppedReason: stoppedReason,
      stopCode: stopCode
    }'
fi

# Search application logs for memory errors
aws logs filter-log-events \
  --log-group-name /ecs/selfpublisherforge-production/spf-api \
  --start-time $(date -d '1 hour ago' +%s000) \
  --filter-pattern '"OutOfMemoryError" OR "MemoryError" OR "OOMKilled" OR "Cannot allocate memory"' \
  --query 'events[].message' \
  --limit 10
```

#### 3. Check task definition memory limits

```bash
# View current memory allocation for the API task
aws ecs describe-task-definition \
  --task-definition spf-api \
  --query 'taskDefinition.containerDefinitions[0].{
    memory: memory,
    memoryReservation: memoryReservation,
    cpu: cpu
  }'

# View current memory allocation for the worker task
aws ecs describe-task-definition \
  --task-definition spf-celery-worker \
  --query 'taskDefinition.containerDefinitions[0].{
    memory: memory,
    memoryReservation: memoryReservation,
    cpu: cpu
  }'
```

## Resolution

### Redis: Immediate memory relief

1. **Clear expired keys** (safe operation):
   ```bash
   # Force Redis to scan and expire keys
   redis-cli -h <redis-endpoint> -p 6379 SCAN 0 COUNT 10000 > /dev/null
   ```

2. **Purge Celery task result metadata** (accumulates over time):
   ```bash
   # Count celery task result keys
   redis-cli -h <redis-endpoint> -p 6379 --scan --pattern "celery-task-meta-*" | wc -l

   # Delete them in batches (these are completed task results, safe to remove)
   redis-cli -h <redis-endpoint> -p 6379 --scan --pattern "celery-task-meta-*" \
     | xargs -L 100 redis-cli -h <redis-endpoint> -p 6379 DEL
   ```

3. **Purge non-critical caches** (adjust patterns to match your key naming):
   ```bash
   # Delete view/fragment cache keys
   redis-cli -h <redis-endpoint> -p 6379 --scan --pattern "cache:views:*" \
     | xargs -L 100 redis-cli -h <redis-endpoint> -p 6379 DEL

   # Delete sessions without TTLs (potential leak)
   redis-cli -h <redis-endpoint> -p 6379 --scan --pattern "session:*" | while read key; do
     ttl=$(redis-cli -h <redis-endpoint> -p 6379 TTL "$key")
     if [ "$ttl" -eq "-1" ]; then
       redis-cli -h <redis-endpoint> -p 6379 DEL "$key"
     fi
   done
   ```

4. **Reduce Celery queue** if backed up (see [celery-queue-depth.md](celery-queue-depth.md)):
   ```bash
   redis-cli -h <redis-endpoint> -p 6379 LLEN celery
   ```

### Redis: Scale the instance

1. **Increase the ElastiCache instance size:**
   ```bash
   aws elasticache modify-replication-group \
     --replication-group-id selfpublisherforge-production-redis \
     --cache-node-type cache.r6g.large \
     --apply-immediately
   ```
   **Note:** This causes a brief failover. Schedule during low-traffic periods if possible.

2. **Adjust maxmemory** if the instance has headroom:
   ```bash
   aws elasticache modify-cache-parameter-group \
     --cache-parameter-group-name selfpublisherforge-production-redis-params \
     --parameter-name-values "ParameterName=maxmemory-policy,ParameterValue=allkeys-lru"
   ```

### Redis: Long-term fixes

- Ensure all cached keys have appropriate TTLs. Audit for keys with `TTL == -1` (no expiry).
- Set `result_expires` in the Celery configuration to auto-expire task result metadata (e.g., `result_expires = 3600`).
- Use `--bigkeys` output to identify and optimize large values (consider compression or smaller serialization).
- Consider splitting cache and broker/session data into separate Redis instances for isolation.
- Monitor the `RedisCacheHitRateLow` (P3) alert as an early indicator of cache pressure.

### ECS Container: Immediate relief

1. **Scale out** to distribute memory pressure:
   ```bash
   CURRENT=$(aws ecs describe-services \
     --cluster selfpublisherforge-production \
     --services spf-api \
     --query 'services[0].desiredCount' --output text)

   aws ecs update-service \
     --cluster selfpublisherforge-production \
     --service spf-api \
     --desired-count $((CURRENT + 2))
   ```

2. **Force restart** to reclaim leaked memory:
   ```bash
   aws ecs update-service \
     --cluster selfpublisherforge-production \
     --service spf-api \
     --force-new-deployment
   ```

3. **Increase container memory limits** by registering a new task definition revision with higher `memory` values and updating the service.

### ECS Container: Long-term fixes

- Profile the application for memory leaks using `tracemalloc` or `memory_profiler` (Python).
- Add `maxsize` parameter to all `@lru_cache` decorators.
- Ensure file uploads stream to disk or S3 rather than buffering entirely in memory.
- Confirm Django `DEBUG = False` in production (when `True`, Django stores all SQL queries in memory).
- Review gunicorn configuration: `--max-requests` and `--max-requests-jitter` to periodically recycle worker processes and reclaim leaked memory.
- Consider `--preload` flag for gunicorn to share application memory between worker processes via copy-on-write.

## Escalation

| Condition                                            | Escalate To                       |
|------------------------------------------------------|-----------------------------------|
| Redis at >95% memory and evictions accelerating       | Infrastructure Lead               |
| Redis rejecting writes (`OOM` errors in logs)         | Infrastructure Lead + Engineering Lead |
| Recurring OOM kills on API or worker containers       | Backend Engineering Lead          |
| Memory leak suspected but cause unknown               | Backend Engineering Lead          |
| Customer-visible impact from cache or memory issues   | Engineering Lead                  |

### Communication

- Post in `#incidents` with current memory utilization percentages and trend direction.
- For Redis write failures: escalate immediately as this affects Celery task submission and cache writes.
- Monitor the Grafana Redis dashboard for recovery trends after applying fixes.
- After resolution, create a post-incident review if Redis exceeded 95% or OOM kills occurred.

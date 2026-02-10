# RedisMemoryUsageCritical Runbook

## Alert
**Name**: RedisMemoryUsageCritical
**Severity**: P1
**Fires when**: Redis memory usage exceeds 90% of the maximum configured memory on the `selfpublisherforge-production-redis` instance, sustained for 10 minutes.

## Impact
Redis is running critically low on memory. Cache evictions are likely occurring aggressively via the LRU eviction policy, which degrades cache hit rates and increases load on the database. If memory is fully exhausted and no eviction policy is set, Redis may reject write commands, breaking Celery task queuing and session management.

## Investigation Steps
1. Check current Redis memory usage and configuration: `redis-cli -h <redis-host> INFO memory`. Look at `used_memory`, `maxmemory`, and `maxmemory_policy`.
2. Check eviction metrics: `redis-cli -h <redis-host> INFO stats | grep evicted_keys`. A high eviction count confirms memory pressure.
3. Identify the largest keys consuming memory: `redis-cli -h <redis-host> --bigkeys`. This scans for the largest keys in each data type.
4. Check if a specific key pattern is growing unexpectedly. Group keys by prefix to identify which application feature is consuming the most memory.
5. Review if the Celery result backend is storing too many task results. Old task results that are never cleaned up can accumulate.

## Resolution
### Common Causes
- **Celery result backend accumulation**: If Celery task results are stored in Redis without TTL, they accumulate indefinitely. Configure `result_expires` in Celery settings to automatically expire old results.
- **Cache key explosion**: A code change may have introduced a new caching pattern that generates too many unique keys. Identify the pattern and add appropriate TTLs or consolidate keys.
- **Session data growth**: If user sessions are stored in Redis, a traffic increase or session TTL misconfiguration can cause memory growth. Review session TTL settings.
- **Memory leak in application caching logic**: A bug may cause data to be cached but never evicted. Review recent code changes to caching logic.
- **Undersized Redis instance**: If legitimate usage has grown, scale up the ElastiCache instance type to one with more memory.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Set appropriate TTLs on all cached keys. Never cache data without an expiration.
- Configure Celery `result_expires` to automatically clean up old task results.
- Monitor Redis memory usage trends and scale proactively before reaching critical levels.
- Implement a `maxmemory-policy` (e.g., `allkeys-lru`) to ensure Redis can evict keys under memory pressure rather than rejecting writes.
- Review and audit cache key patterns during code reviews to prevent key explosion.

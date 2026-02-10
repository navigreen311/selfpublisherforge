# RedisCacheHitRateLow Runbook

## Alert
**Name**: RedisCacheHitRateLow
**Severity**: P3
**Fires when**: The Redis cache hit rate falls below 80% (hits / (hits + misses)) over a 1-hour window, sustained for 1 hour.

## Impact
A lower-than-expected cache hit rate means more requests are falling through to the database or other backend services. This increases latency for affected requests and puts additional load on the database. While not immediately critical, a sustained low hit rate degrades overall performance and may lead to latency or database CPU alerts.

## Investigation Steps
1. Check the current hit rate and compare to historical baselines: `redis-cli -h <redis-host> INFO stats | grep keyspace`. Calculate hit rate from `keyspace_hits` and `keyspace_misses`.
2. Check if the cache was recently flushed or if Redis was recently restarted. A cold cache will naturally have a low hit rate until it warms up.
3. Check Redis memory usage and eviction metrics: `redis-cli -h <redis-host> INFO stats | grep evicted_keys`. High evictions due to memory pressure will lower the hit rate.
4. Review application code changes that may have altered caching behavior: new features without caching, changed cache key patterns, reduced TTLs, or removed cache calls.
5. Analyze the types of cache misses. Determine if they are compulsory misses (first access), capacity misses (evicted due to memory), or invalidation misses (expired TTLs).

## Resolution
### Common Causes
- **Cold cache after restart or flush**: Allow time for the cache to warm up. If needed, implement a cache warming strategy that pre-loads frequently accessed data.
- **Memory pressure causing evictions**: If Redis is running low on memory, keys are being evicted before they can be hit. Scale up the Redis instance or reduce the data stored (see the `redis-high-memory` runbook).
- **TTL too short**: If cache TTLs are set too aggressively short, data expires before it can be reused. Review and extend TTLs where appropriate.
- **New features without caching**: Recent code changes may have added new database queries without corresponding cache integration. Add caching for high-frequency, read-heavy queries.
- **Changed access patterns**: User behavior changes may have shifted which data is frequently accessed, invalidating the existing cache strategy. Review and adapt cache key patterns.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Monitor cache hit rates per key prefix to identify which features have poor cache performance.
- Set appropriate TTLs based on data update frequency and access patterns.
- Implement cache warming strategies for predictable high-traffic patterns.
- Ensure all read-heavy database queries have a caching layer.
- Right-size Redis instance memory to minimize eviction-driven cache misses.

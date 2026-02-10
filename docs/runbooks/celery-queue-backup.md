# CeleryQueueDepthCritical Runbook

## Alert
**Name**: CeleryQueueDepthCritical
**Severity**: P1
**Fires when**: The Celery queue depth exceeds 500 tasks in production, sustained for 10 minutes.

## Impact
Background job processing is severely backed up. Users may experience delays in operations that rely on asynchronous processing, such as book generation, email notifications, file exports, and other queued tasks. The backlog may continue to grow if not addressed.

## Investigation Steps
1. Check the current queue depth and breakdown by queue name. Use the Celery monitoring tool (Flower) or query Redis directly: `redis-cli -h <redis-host> LLEN <queue-name>`.
2. Check the Celery worker status and count. Verify that workers are running and consuming tasks: `celery -A selfpublisherforge inspect active`.
3. Review Celery worker logs for errors, stuck tasks, or tasks that are taking abnormally long to complete.
4. Check if a specific task type is dominating the queue. A single misbehaving task type can block processing of all other tasks.
5. Verify Redis health and connectivity. If Redis is slow or unreachable, workers cannot dequeue tasks.

## Resolution
### Common Causes
- **Insufficient workers**: Scale up the number of Celery worker tasks in ECS: `aws ecs update-service --cluster selfpublisherforge-production --service selfpublisherforge-worker-production --desired-count <new-count>`.
- **Stuck or long-running tasks**: Identify and terminate stuck tasks. If a specific task type is stuck, investigate the root cause (e.g., external API timeout, database lock). Set appropriate task time limits using `task_time_limit` and `task_soft_time_limit`.
- **Worker crash loop**: Check ECS task logs and events for worker containers that are repeatedly crashing. Fix the underlying issue (OOM, dependency failure, code bug) and redeploy.
- **Burst of task submissions**: If a batch operation or cron job submitted a large number of tasks at once, the queue will naturally drain as workers process them. Monitor the drain rate and scale workers if needed.
- **Redis performance degradation**: If Redis is slow, task dequeuing will be slow. Check Redis CPU, memory, and network metrics.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Configure auto-scaling for Celery worker ECS tasks based on queue depth.
- Set appropriate task time limits and soft time limits to prevent tasks from running indefinitely.
- Implement task rate limiting for batch operations to prevent queue flooding.
- Monitor queue depth trends with the P3 alert (100 tasks threshold) to catch growing queues early.
- Use dedicated queues for different task priorities to ensure critical tasks are processed even during backlogs.

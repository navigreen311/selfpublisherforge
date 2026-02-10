# CeleryQueueGrowingTrend Runbook

## Alert
**Name**: CeleryQueueGrowingTrend
**Severity**: P3
**Fires when**: The Celery queue depth exceeds 100 tasks in production, sustained for 1 hour.

## Impact
The Celery queue has been above 100 tasks for an extended period, indicating that task production rate is outpacing consumption. While users may not notice immediate impact, sustained queue growth will eventually lead to significant delays in background processing. If unaddressed, this may escalate to the P1 critical queue depth alert (500 tasks).

## Investigation Steps
1. Check the current queue depth and whether it is growing, stable, or shrinking. Review the queue depth metric over the last few hours to understand the trend.
2. Check Celery worker count and their processing rate. Verify that workers are actively consuming tasks and not idle or stuck.
3. Identify which task types are most prevalent in the queue. Determine if a specific task type is being submitted faster than it can be processed.
4. Review if a cron job or batch operation is submitting a large number of tasks. Check the task submission rate over time.
5. Check worker resource utilization (CPU, memory) to determine if workers are running at capacity.

## Resolution
### Common Causes
- **Insufficient worker count**: The current number of workers cannot keep up with the task submission rate. Increase the worker task count: `aws ecs update-service --cluster selfpublisherforge-production --service selfpublisherforge-worker-production --desired-count <new-count>`.
- **Slow task execution**: Individual tasks are taking longer than expected, reducing throughput. Profile the slowest task types and optimize their execution time.
- **Batch job submission**: A periodic batch job submitted many tasks at once. If this is expected, the queue will drain naturally. Consider rate-limiting batch submissions.
- **New feature generating more tasks**: A recently deployed feature may be generating more background tasks than anticipated. Review the feature's task submission logic.
- **Worker concurrency too low**: Each worker process handles a limited number of concurrent tasks. Increase the `--concurrency` setting on workers if resources allow.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Configure auto-scaling for Celery worker ECS tasks based on queue depth metrics.
- Implement task rate limiting for batch operations.
- Monitor queue depth trends and set up dashboards for visibility.
- Optimize task execution time to maximize worker throughput.
- Use task priorities to ensure critical tasks are processed first, even during periods of high queue depth.

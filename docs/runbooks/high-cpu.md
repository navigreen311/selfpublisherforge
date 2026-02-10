# HighCPUUsageSustained Runbook

## Alert
**Name**: HighCPUUsageSustained
**Severity**: P3
**Fires when**: Average CPU usage for an ECS service in the `selfpublisherforge-production` cluster exceeds 70%, sustained for 1 hour.

## Impact
An ECS service is running at high CPU utilization for an extended period. While the service is still functioning, it has limited headroom to handle traffic spikes. Sustained high CPU usage may also indicate an inefficiency in the application that is wasting resources and increasing costs.

## Investigation Steps
1. Identify which ECS service is affected from the alert labels (`container_label_com_amazonaws_ecs_service_name`). Check the service's current task count and CPU utilization across all tasks.
2. Review the application's CPU profile. If APM is available, check which functions or endpoints are consuming the most CPU time.
3. Correlate the high CPU with traffic patterns. Check if traffic has increased significantly or if CPU usage is disproportionate to the request rate.
4. Review recent deployments for code changes that may have introduced CPU-intensive operations or removed optimizations.
5. Check if auto-scaling policies are configured and whether they should have triggered additional tasks.

## Resolution
### Common Causes
- **Increased traffic without scaling**: Traffic has grown beyond the current task count's capacity. Scale out the service by increasing the desired task count or configure auto-scaling based on CPU utilization.
- **Inefficient code or algorithm**: A recent code change introduced a CPU-intensive operation (e.g., inefficient loop, large data processing, regex backtracking). Profile the application and optimize the hot path.
- **Missing caching**: Computations that could be cached are being recalculated on every request. Add caching for expensive operations.
- **Logging or serialization overhead**: Excessive logging, JSON serialization, or response processing can consume significant CPU. Review and optimize.
- **Background processing on API tasks**: If background tasks are running in the same process as API handlers, they compete for CPU. Separate background processing into dedicated worker tasks.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Configure CPU-based auto-scaling policies to automatically scale ECS services when CPU exceeds 60%.
- Conduct regular performance profiling and optimization reviews.
- Implement caching for computationally expensive operations.
- Set up dashboards to track CPU utilization trends over time.
- Right-size ECS task CPU allocations based on actual usage patterns.

# ECSTaskRestarts Runbook

## Alert
**Name**: ECSTaskRestarts
**Severity**: P2
**Fires when**: An ECS service in the `selfpublisherforge-production` cluster has more than 5 task restarts within a 30-minute window.

## Impact
Frequent task restarts indicate instability in one or more services. While ECS will continue restarting tasks and the service may remain partially available, each restart causes a brief disruption. Users may experience intermittent errors or slow responses during restart cycles.

## Investigation Steps
1. Identify which ECS service is experiencing restarts. Check the alert labels for `service_name`, then review the service's events: `aws ecs describe-services --cluster selfpublisherforge-production --services <service-name>`.
2. Check the stopped task reasons: `aws ecs list-tasks --cluster selfpublisherforge-production --service-name <service-name> --desired-status STOPPED` and then describe each stopped task to see the stop reason.
3. Review CloudWatch container logs for the crashing tasks. Look for unhandled exceptions, out-of-memory errors, or dependency connection failures.
4. Check if the task is being OOM-killed by comparing the container's memory usage against its memory limit in the task definition.
5. Verify that health check endpoints are responding correctly and within the configured timeout and interval.

## Resolution
### Common Causes
- **Out of memory (OOM) kills**: The container is exceeding its memory limit. Increase the memory limit in the task definition or fix the memory leak in the application.
- **Application crash on startup**: The application may be failing during initialization (e.g., missing environment variables, database migration failure, invalid configuration). Check container logs for startup errors.
- **Health check failures**: The container starts but the health check endpoint fails. Verify the health check path, port, timeout, and grace period configuration.
- **Dependency unavailability**: If a required service (database, Redis) is unavailable during startup, the application may crash. Add retry logic for dependency connections during startup.
- **Bad deployment**: If restarts started after a deployment, roll back to the previous task definition version.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Set appropriate memory limits with headroom for peak usage.
- Configure health check grace periods to allow sufficient startup time.
- Implement graceful startup with retry logic for dependency connections.
- Enable ECS circuit breaker to automatically roll back deployments that cause task failures.
- Add startup probes and readiness checks to distinguish between slow starts and actual failures.

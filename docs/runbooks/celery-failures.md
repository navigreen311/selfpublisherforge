# CeleryTaskFailureRate Runbook

## Alert
**Name**: CeleryTaskFailureRate
**Severity**: P2
**Fires when**: The Celery task failure rate exceeds 5% of total tasks (failed / (succeeded + failed)) over a 15-minute window, sustained for 15 minutes.

## Impact
A significant portion of background tasks are failing. Depending on which tasks are failing, users may experience missing email notifications, failed book generations, incomplete file exports, or other features that rely on asynchronous processing.

## Investigation Steps
1. Identify which task types are failing. Check Celery Flower dashboard or query task metrics by task name to find the task types with the highest failure rates.
2. Review worker logs for the failing task types. Look for exception tracebacks, timeout errors, or dependency connection failures.
3. Check if the failures are caused by a specific input or data condition. Some tasks may fail only for certain user data or edge cases.
4. Verify health of services that tasks depend on: database, Redis, external APIs, file storage (S3).
5. Check if a recent deployment introduced the failures by correlating the failure spike with deployment timestamps.

## Resolution
### Common Causes
- **Dependency unavailability**: Tasks fail because a downstream service (database, external API, S3) is unreachable or returning errors. Address the dependency issue first.
- **Task timeout**: Tasks are exceeding their time limit due to slow operations. Increase the timeout if appropriate, or optimize the task logic.
- **Code bug in task logic**: A recent code change introduced a bug in one or more task types. Identify the bug from the exception traceback and deploy a fix.
- **Data-dependent failures**: Specific data conditions cause tasks to fail (e.g., malformed input, missing required fields). Add input validation and error handling to make tasks more resilient.
- **Resource exhaustion on workers**: If workers are running out of memory or CPU, tasks may fail or be killed. Scale up worker resources or reduce concurrency.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Implement automatic retries with exponential backoff for transient failures.
- Add comprehensive error handling and input validation to all task types.
- Use dead letter queues to capture and analyze permanently failed tasks.
- Monitor task failure rates per task type to quickly identify regressions.
- Test task logic thoroughly, including edge cases and error scenarios, before deployment.

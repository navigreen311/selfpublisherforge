# Runbook: API Service Down

## Alert

| Field       | Value                                                      |
|-------------|------------------------------------------------------------|
| Alert Name  | `APIServiceDown`                                           |
| Expression  | `up{job="spf-api"} == 0` for 5 minutes                    |
| Severity    | **P0 -- Critical**                                         |
| Service     | `api`                                                      |
| Environment | `production`                                               |
| Runbook URL | `docs/runbooks/api-service-down.md`                        |

Fires when the Prometheus scrape target for the SelfPublisherForge API (`spf-api`) has been unreachable for more than 5 minutes, indicating the API service has zero running tasks or is completely unreachable.

## Impact

- **Full service outage.** All user-facing functionality is unavailable.
- HTTP requests to the API return 502/503 from the Application Load Balancer.
- Dependent services (frontend, mobile clients, third-party integrations) cannot communicate with the backend.
- Background workers may continue processing but cannot write results through the API.
- Revenue-impacting: users cannot purchase, publish, or manage books.

## Investigation

### 1. Confirm the outage

```bash
# Health check from outside the VPC
curl -sS -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" \
  https://api.selfpublisherforge.com/health

# Health check from within the VPC (bypasses ALB)
curl -sS -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" \
  http://<internal-alb-dns>:8000/health
```

### 2. Check ECS task status

```bash
# Check running tasks for the API service
aws ecs list-tasks \
  --cluster selfpublisherforge-production \
  --service-name spf-api \
  --desired-status RUNNING \
  --output table

# Check desired vs running count and recent service events
aws ecs describe-services \
  --cluster selfpublisherforge-production \
  --services spf-api \
  --query 'services[0].{
    desiredCount: desiredCount,
    runningCount: runningCount,
    pendingCount: pendingCount,
    status: status,
    events: events[:5]
  }'

# Inspect recently stopped tasks for stop reasons
STOPPED_TASKS=$(aws ecs list-tasks \
  --cluster selfpublisherforge-production \
  --service-name spf-api \
  --desired-status STOPPED \
  --query 'taskArns[:3]' --output text)

if [ -n "$STOPPED_TASKS" ]; then
  aws ecs describe-tasks \
    --cluster selfpublisherforge-production \
    --tasks $STOPPED_TASKS \
    --query 'tasks[].{
      taskArn: taskArn,
      lastStatus: lastStatus,
      stoppedReason: stoppedReason,
      stopCode: stopCode,
      stoppedAt: stoppedAt
    }'
fi
```

### 3. Check CloudWatch logs for crash output

```bash
# Tail recent API logs
aws logs tail /ecs/selfpublisherforge-production/spf-api \
  --since 30m \
  --format short

# Search for fatal errors, OOM kills, and stack traces
aws logs filter-log-events \
  --log-group-name /ecs/selfpublisherforge-production/spf-api \
  --start-time $(date -d '30 minutes ago' +%s000) \
  --filter-pattern '"FATAL" OR "OOMKilled" OR "OutOfMemoryError" OR "Traceback"' \
  --query 'events[].message' \
  --limit 20
```

### 4. Check the Application Load Balancer

```bash
# Check target group health
aws elbv2 describe-target-health \
  --target-group-arn <spf-api-target-group-arn> \
  --query 'TargetHealthDescriptions[].{
    Target: Target.Id,
    Port: Target.Port,
    Health: TargetHealth.State,
    Reason: TargetHealth.Reason
  }' --output table

# Check for 5xx spikes on the ALB (last 30 minutes, 1-minute intervals)
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name HTTPCode_ELB_5XX_Count \
  --dimensions Name=LoadBalancer,Value=<alb-name> \
  --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum
```

### 5. Check for infrastructure issues

```bash
# Verify the ECS cluster health
aws ecs describe-clusters \
  --clusters selfpublisherforge-production \
  --query 'clusters[0].{
    status: status,
    registeredContainerInstancesCount: registeredContainerInstancesCount,
    activeServicesCount: activeServicesCount,
    runningTasksCount: runningTasksCount
  }'

# Check if the container image is pullable
aws ecr describe-images \
  --repository-name selfpublisherforge/api \
  --query 'imageDetails | sort_by(@, &imagePushedAt) | [-1].{
    tags: imageTags,
    pushedAt: imagePushedAt,
    sizeBytes: imageSizeInBytes
  }'
```

### 6. Check recent deployments

```bash
# List deployment history
aws ecs describe-services \
  --cluster selfpublisherforge-production \
  --services spf-api \
  --query 'services[0].deployments[].{
    id: id,
    status: status,
    taskDefinition: taskDefinition,
    desiredCount: desiredCount,
    runningCount: runningCount,
    createdAt: createdAt
  }'
```

## Resolution

### Bad deployment or application crash

1. Identify the previous working task definition revision:
   ```bash
   aws ecs list-task-definitions \
     --family-prefix spf-api \
     --sort DESC \
     --query 'taskDefinitionArns[:3]'
   ```

2. Roll back to the previous revision:
   ```bash
   aws ecs update-service \
     --cluster selfpublisherforge-production \
     --service spf-api \
     --task-definition spf-api:<previous-revision-number>
   ```

3. Monitor for task startup:
   ```bash
   watch -n 5 'aws ecs describe-services \
     --cluster selfpublisherforge-production \
     --services spf-api \
     --query "services[0].{desired:desiredCount,running:runningCount,pending:pendingCount}"'
   ```

### Container image pull failure

1. Verify the image exists in ECR and the tag is correct.
2. Check the ECS task execution role has `ecr:GetDownloadUrlForLayer` and `ecr:BatchGetImage` permissions.
3. Verify VPC endpoints or NAT gateway connectivity to ECR.

### OOM killed (Out of Memory)

1. Check the task definition memory limits:
   ```bash
   aws ecs describe-task-definition \
     --task-definition spf-api \
     --query 'taskDefinition.containerDefinitions[0].{memory:memory,memoryReservation:memoryReservation}'
   ```
2. If legitimate memory growth, increase the memory allocation in the task definition.
3. If a memory leak, see [high-memory-usage.md](high-memory-usage.md).

### Health check failure

1. Verify the `/health` endpoint works when the container starts.
2. Check that the health check grace period allows enough time for application startup.
3. Review the health check configuration on the target group:
   ```bash
   aws elbv2 describe-target-groups \
     --target-group-arns <spf-api-target-group-arn> \
     --query 'TargetGroups[0].{
       HealthCheckPath: HealthCheckPath,
       HealthCheckIntervalSeconds: HealthCheckIntervalSeconds,
       HealthyThresholdCount: HealthyThresholdCount,
       UnhealthyThresholdCount: UnhealthyThresholdCount
     }'
   ```

### Tasks not scheduling at all

1. Force a new deployment:
   ```bash
   aws ecs update-service \
     --cluster selfpublisherforge-production \
     --service spf-api \
     --force-new-deployment
   ```
2. Check for capacity issues (Fargate capacity, subnet IP exhaustion).
3. Check security groups allow traffic on the application port (8000).

## Escalation

| Condition                                      | Escalate To                      |
|------------------------------------------------|----------------------------------|
| Unable to restore service within 15 minutes    | Engineering Lead                 |
| Root cause is AWS infrastructure (ECS, ALB)    | AWS Support (Severity 1)        |
| Root cause is a bad deployment                 | Deploying engineer               |
| Data integrity concerns after outage           | Database Lead                    |
| Customer-visible outage exceeding 30 minutes   | VP Engineering + CTO             |

### Communication

- Post a status update in `#incidents` Slack channel immediately upon alert firing.
- If customer-facing impact exceeds 5 minutes, notify the Customer Success team.
- Update the status page at https://status.selfpublisherforge.com.
- For outages exceeding 15 minutes, open a bridge call.
- After resolution, create a post-incident review document.

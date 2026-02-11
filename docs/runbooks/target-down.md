# Runbook: Target Down

## Alert

| Field       | Value                                                      |
|-------------|------------------------------------------------------------|
| Alert Name  | `TargetDown`                                               |
| Expression  | `up == 0` for 5 minutes                                   |
| Severity    | **P0 -- Critical**                                         |
| Service     | `monitoring`                                               |
| Environment | `production`                                               |
| Runbook URL | `docs/runbooks/target-down.md`                             |

Fires when any Prometheus scrape target has been unreachable for more than 5 minutes. The `up` metric is automatically generated for every scrape target: `1` means the scrape succeeded, `0` means it failed.

## Severity

**P0 -- Critical.** A scrape target being down means Prometheus is unable to collect metrics from that service. This creates blind spots in monitoring and may indicate that the underlying service itself is down.

## Symptoms

- Prometheus shows `up == 0` for the affected target in the Targets page.
- Metrics from the affected service stop updating and become stale.
- Dashboards relying on the affected target's metrics show "No Data" or stale values.
- Other alerts that depend on metrics from the downed target may fail to fire (silent failures).
- The alert summary identifies the specific `job` and `instance` that are unreachable.

## Investigation Steps

### 1. Identify the affected target

Check the alert labels to determine which scrape target is down. The `job` and `instance` labels identify the target.

```bash
# Check Prometheus targets page for current status
curl -sS http://localhost:9090/api/v1/targets | \
  jq '.data.activeTargets[] | select(.health == "down") | {job: .labels.job, instance: .scrapeUrl, lastError: .lastError}'
```

### 2. Check if the target's Docker container is running

```bash
# List all containers and their status
docker ps -a --filter "name=spf-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check if the specific service container is running (replace <service-name>)
docker inspect --format='{{.State.Status}} (exit code: {{.State.ExitCode}})' <container-name>

# Check container logs for crash output
docker logs --tail 50 --timestamps <container-name>
```

### 3. Check ECS task status (if running on ECS)

```bash
# List running tasks across all services
aws ecs list-tasks \
  --cluster selfpublisherforge-production \
  --desired-status RUNNING \
  --output table

# Check specific service status
aws ecs describe-services \
  --cluster selfpublisherforge-production \
  --services <service-name> \
  --query 'services[0].{
    desiredCount: desiredCount,
    runningCount: runningCount,
    pendingCount: pendingCount,
    status: status,
    events: events[:5]
  }'
```

### 4. Verify network connectivity

```bash
# Test connectivity from the Prometheus host to the target
curl -sS -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" \
  http://<target-host>:<target-port>/metrics

# Check DNS resolution
nslookup <target-hostname>

# Check if the port is open
nc -zv <target-host> <target-port>
```

### 5. Check the service health endpoint

```bash
# Hit the service's health endpoint directly
curl -sS http://<target-host>:<target-port>/health

# Check service logs for errors
aws logs tail /ecs/selfpublisherforge-production/<service-name> \
  --since 15m \
  --format short
```

### 6. Verify Prometheus scrape configuration

```bash
# Check that the target is correctly defined in prometheus.yml
grep -A 10 "<job-name>" /etc/prometheus/prometheus.yml

# Reload Prometheus configuration if it was recently changed
curl -X POST http://localhost:9090/-/reload
```

## Resolution

### Service container is stopped or crashed

1. Restart the container or ECS task:
   ```bash
   # Docker restart
   docker restart <container-name>

   # ECS: force a new deployment
   aws ecs update-service \
     --cluster selfpublisherforge-production \
     --service <service-name> \
     --force-new-deployment
   ```

2. Investigate the root cause of the crash in the container logs.

### Network connectivity issue

1. Verify security groups allow inbound traffic on the metrics port from the Prometheus instance.
2. Check that the service is bound to the correct network interface (not just `127.0.0.1`).
3. Verify VPC routing and subnet configuration if services are in different subnets.

### Metrics endpoint not responding

1. Verify the `/metrics` endpoint is enabled in the service configuration.
2. Check that the metrics exporter sidecar (if applicable) is running.
3. Confirm the scrape port matches the port the service is exposing metrics on.

### Scrape configuration mismatch

1. Confirm the `prometheus.yml` scrape target host/port matches the actual service.
2. If the service was redeployed with a new IP or port, update the Prometheus configuration and reload.

## Escalation

| Condition                                                | Escalate To                      |
|----------------------------------------------------------|----------------------------------|
| Target is a critical service (API, database) and is down | Follow the service-specific runbook (e.g., [api-service-down.md](api-service-down.md)) |
| Multiple targets are down simultaneously                 | Engineering Lead                 |
| Network-level issue affecting connectivity               | Infrastructure / DevOps Lead     |
| Unable to restore the target within 15 minutes           | Engineering Lead                 |
| Prometheus itself is having issues                       | DevOps / SRE team                |

### Communication

- Post a status update in `#incidents` Slack channel if the downed target is a user-facing service.
- If the downed target results in a user-visible outage, follow the service-specific runbook for communication procedures.
- After resolution, verify all dependent alerts and dashboards are receiving fresh data.

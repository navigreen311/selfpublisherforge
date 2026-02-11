# Runbook: Watchdog

## Alert

| Field       | Value                                                      |
|-------------|------------------------------------------------------------|
| Alert Name  | `Watchdog`                                                 |
| Expression  | `vector(1)` (always fires)                                 |
| Severity    | **none** (meta-alert)                                      |
| Service     | `monitoring`                                               |
| Environment | `production`                                               |
| Runbook URL | `docs/runbooks/watchdog.md`                                |

This is a dead man's switch alert. It fires continuously to verify the entire alerting pipeline (Prometheus -> AlertManager -> notification receiver) is functional. **If this alert STOPS firing, it means the alerting pipeline itself is broken** and no other alerts will be delivered.

## Severity

**Meta-alert -- no severity tier.** This alert has no direct user impact when it is firing. The critical event is when this alert **stops** firing, which means the alerting infrastructure is broken and all other alerts are silently failing.

## Symptoms

When the Watchdog alert stops firing:

- No alert notifications are being delivered to any channel (Slack, PagerDuty, email).
- The alerting pipeline has a silent failure -- services could be down with no one being notified.
- The Watchdog receiver (if configured) stops receiving the periodic heartbeat.
- AlertManager UI may show no active alerts, or may be unreachable entirely.
- Prometheus Alerts page may show the Watchdog rule as inactive or missing.

## Investigation Steps

### 1. Check Prometheus is running and healthy

```bash
# Verify Prometheus is reachable
curl -sS http://localhost:9090/-/healthy
# Expected: "Prometheus Server is Healthy."

# Check Prometheus is ready to serve traffic
curl -sS http://localhost:9090/-/ready
# Expected: "Prometheus Server is Ready."

# Check Prometheus process status
docker ps --filter "name=prometheus" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### 2. Verify the Watchdog rule is loaded and active

```bash
# Check all loaded alerting rules
curl -sS http://localhost:9090/api/v1/rules | \
  jq '.data.groups[].rules[] | select(.name == "Watchdog") | {name: .name, state: .state, health: .health}'

# Verify the alerts.yml file is correctly mounted/loaded
curl -sS http://localhost:9090/api/v1/status/config | \
  jq '.data.yaml' | grep -i "watchdog"
```

### 3. Check AlertManager is running and reachable

```bash
# Verify AlertManager is reachable
curl -sS http://localhost:9093/-/healthy
# Expected: "OK"

# Check AlertManager process status
docker ps --filter "name=alertmanager" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check active alerts in AlertManager
curl -sS http://localhost:9093/api/v2/alerts | jq '.[].labels.alertname'
```

### 4. Verify Prometheus can reach AlertManager

```bash
# Check Prometheus alertmanager configuration and connectivity
curl -sS http://localhost:9090/api/v1/alertmanagers | \
  jq '.data.activeAlertmanagers'

# If empty, Prometheus cannot reach AlertManager. Check the alerting
# configuration in prometheus.yml:
grep -A 5 "alerting:" /etc/prometheus/prometheus.yml
```

### 5. Check AlertManager notification configuration

```bash
# Verify AlertManager configuration is valid
docker exec alertmanager amtool check-config /etc/alertmanager/alertmanager.yml

# Check AlertManager logs for notification delivery errors
docker logs --tail 100 --timestamps alertmanager 2>&1 | grep -i "error\|fail\|notify"

# Test notification delivery manually
docker exec alertmanager amtool alert add test-alert severity=none \
  --annotation=summary="Test alert from watchdog investigation"
```

### 6. Check for resource issues

```bash
# Check if Prometheus or AlertManager are OOM-killed or resource-starved
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" \
  prometheus alertmanager

# Check disk space on the Prometheus data volume
df -h /var/lib/prometheus
```

## Resolution

### Prometheus is down or unhealthy

1. Restart Prometheus:
   ```bash
   docker restart prometheus
   ```
2. If Prometheus fails to start, check logs for configuration errors:
   ```bash
   docker logs --tail 100 prometheus
   ```
3. Validate the Prometheus configuration:
   ```bash
   docker exec prometheus promtool check config /etc/prometheus/prometheus.yml
   ```

### AlertManager is down or unreachable

1. Restart AlertManager:
   ```bash
   docker restart alertmanager
   ```
2. Verify the AlertManager configuration is valid:
   ```bash
   docker exec alertmanager amtool check-config /etc/alertmanager/alertmanager.yml
   ```
3. Ensure Prometheus `alerting.alertmanagers` config points to the correct AlertManager address.

### Alerting rules not loaded

1. Verify `rule_files` in `prometheus.yml` includes the alerts configuration file.
2. Check file permissions on the alerts YAML file.
3. Validate the rules file syntax:
   ```bash
   docker exec prometheus promtool check rules /etc/prometheus/alerts.yml
   ```
4. Reload Prometheus configuration:
   ```bash
   curl -X POST http://localhost:9090/-/reload
   ```

### Notification receiver is broken

1. Check the AlertManager configuration for the receiver (Slack webhook URL, PagerDuty key, email SMTP settings).
2. Verify external connectivity from the AlertManager container to the notification service.
3. Test the webhook/integration endpoint manually.

### Prometheus storage is full

1. Check disk usage and clean up old data if necessary:
   ```bash
   df -h /var/lib/prometheus
   ```
2. Adjust retention settings in Prometheus startup flags (`--storage.tsdb.retention.time`, `--storage.tsdb.retention.size`).
3. Expand the storage volume if needed.

## Escalation

| Condition                                                  | Escalate To                      |
|------------------------------------------------------------|----------------------------------|
| Alerting pipeline is fully broken (no alerts delivering)   | Engineering Lead + DevOps Lead   |
| Prometheus is down and cannot be restarted                 | DevOps / SRE team                |
| AlertManager configuration issues                         | DevOps / SRE team                |
| Underlying infrastructure issue (disk, network, compute)  | Infrastructure team              |
| Pipeline has been down for more than 30 minutes            | VP Engineering                   |

### Communication

- A broken alerting pipeline is itself a critical incident -- post immediately in `#incidents` Slack channel.
- Manually verify all critical services are healthy while the alerting pipeline is down.
- Consider setting up an external dead man's switch service (e.g., Healthchecks.io, PagerDuty heartbeat) that alerts through an independent channel if the Watchdog heartbeat stops arriving.
- After resolution, verify all pending alerts are delivered and no incidents were missed during the outage.

# W29: Create Runbook Documentation (20 files)

## Branch: `fix/w29-runbook-docs`

## Files YOU Own (only create/modify these):
- `docs/runbooks/` directory (NEW — all files below)

## Task

The `infra/monitoring/alerts.yml` file references 20 runbook URLs that don't exist. Create a `docs/runbooks/` directory with a markdown file for each runbook.

First, read `infra/monitoring/alerts.yml` to find all referenced runbook URLs. They follow the pattern:
```
runbook_url: "https://github.com/navigreen311/selfpublisherforge/wiki/runbooks/<name>"
```

Create a markdown file for each one at `docs/runbooks/<name>.md`. Each runbook should follow this template:

```markdown
# <Alert Name> Runbook

## Alert
**Name**: <Alert name from alerts.yml>
**Severity**: <P0/P1/P2/P3>
**Fires when**: <Condition from the alert rule>

## Impact
<What user-facing or system impact this alert indicates>

## Investigation Steps
1. <Step 1 — check logs, metrics, etc.>
2. <Step 2 — identify root cause>
3. <Step 3 — check dependent services>

## Resolution
### Common Causes
- <Cause 1>: <Fix>
- <Cause 2>: <Fix>
- <Cause 3>: <Fix>

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
<How to prevent this alert from firing in the future>
```

### Expected Files (approximately):
1. `api-service-down.md`
2. `rds-connection-failure.md`
3. `high-error-rate.md`
4. `celery-queue-backup.md`
5. `high-memory-usage.md`
6. `high-cpu-usage.md`
7. `redis-connection-failure.md`
8. `elasticsearch-cluster-health.md`
9. `disk-space-critical.md`
10. `ssl-certificate-expiry.md`
... and all others found in alerts.yml

Also create `docs/runbooks/README.md` with an index linking to all runbooks.

Also update `infra/monitoring/alerts.yml` to change the runbook URLs from the wiki format to relative paths:
```yaml
# BEFORE:
runbook_url: "https://github.com/navigreen311/selfpublisherforge/wiki/runbooks/api-service-down"
# AFTER:
runbook_url: "https://github.com/navigreen311/selfpublisherforge/blob/main/docs/runbooks/api-service-down.md"
```

## Verification
```bash
ls docs/runbooks/*.md | wc -l
# Should be 20+
```

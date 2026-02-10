# DeploymentCompleted Runbook

## Alert
**Name**: DeploymentCompleted
**Severity**: P3
**Fires when**: A new deployment to production is detected (deploy timestamp is less than 5 minutes old).

## Impact
This is an informational alert. A new version of the application has been deployed to production. No immediate user impact is expected if the deployment is healthy. However, this alert serves as a signal to monitor the deployment's health and be prepared to roll back if issues arise.

## Investigation Steps
1. Identify what was deployed. Check the most recent deployment details: commit hash, PR number, and changelog. Review the CI/CD pipeline for the deployment that just completed.
2. Monitor key health metrics for the first 15 minutes after deployment: error rate, latency P95, and response codes. Compare to the pre-deployment baseline.
3. Check that all ECS tasks have successfully transitioned to the new task definition. Verify that no tasks are stuck in a pending or failed state.
4. Review application logs for any new error patterns or warnings that were not present before the deployment.
5. If the deployment included database migrations, verify that they completed successfully and that the application is compatible with the new schema.

## Resolution
### Common Causes
- **Healthy deployment (no action needed)**: If all metrics remain stable after 15 minutes, no action is needed. The alert will auto-resolve.
- **Deployment causing elevated error rate**: If errors increase after deployment, initiate a rollback: `aws ecs update-service --cluster selfpublisherforge-production --service selfpublisherforge-api-production --task-definition <previous-revision>`.
- **Deployment causing latency increase**: If P95 latency increases significantly, investigate the changes in the deployment. Roll back if the latency is unacceptable.
- **Partial deployment (mixed versions)**: If some tasks are running the old version while others have the new version, the deployment may be in progress. Wait for the rollout to complete, but monitor closely.
- **Database migration issue**: If a migration failed or is incompatible, the application may error on specific operations. Check migration status and consider rolling back both the migration and the deployment.

## Escalation
- **P0/P1**: Page on-call engineer immediately
- **P2**: Create ticket, address within 4 hours
- **P3**: Create ticket, address within 24 hours

## Prevention
- Use canary deployments to gradually roll out changes and catch issues early.
- Implement automated rollback triggers based on error rate and latency thresholds.
- Run comprehensive integration tests in staging before promoting to production.
- Maintain a deployment checklist that includes monitoring and verification steps.
- Ensure database migrations are backward-compatible to allow safe rollbacks.

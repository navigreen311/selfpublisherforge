# Deployment Guide

## Environments

| Environment | URL | Branch/Trigger | AWS Account |
|---|---|---|---|
| **Staging** | `https://staging.selfpublisherforge.com` | Push to `main` | Staging AWS |
| **Production** | `https://selfpublisherforge.com` | Tag push `v*.*.*` | Production AWS |

### Environment Differences

| Resource | Staging | Production |
|---|---|---|
| ECS API Tasks | 2 | 2-10 (auto-scaled) |
| ECS Workers | 1 | 2 |
| RDS Instance | db.t3.medium (single-AZ) | db.t3.medium (multi-AZ) |
| Redis | cache.t3.medium (1 node) | cache.t3.medium (1 node) |
| RDS Backups | 7 days | 7 days |
| Deletion Protection | No | Yes |

## Prerequisites

- AWS CLI v2 configured with appropriate credentials
- Docker and Docker Compose installed
- Terraform >= 1.6.0 installed
- Access to the GitHub repository

### Required AWS Secrets (GitHub Actions)

Configure these in **Settings > Secrets and variables > Actions**:

| Secret | Description |
|---|---|
| `AWS_ACCOUNT_ID` | AWS account ID for ECR registry |
| `AWS_DEPLOY_ROLE_ARN` | IAM role ARN for staging deployments |
| `AWS_PROD_DEPLOY_ROLE_ARN` | IAM role ARN for production deployments |
| `STAGING_URL` | Staging environment URL |
| `PRODUCTION_API_URL` | Production API base URL |
| `PROD_TARGET_GROUP_ARN` | ALB target group ARN for health checks |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |

### Required AWS SSM Parameters

Store these in AWS Systems Manager Parameter Store:

```
/selfpublisherforge/<env>/database-url    — PostgreSQL connection string
/selfpublisherforge/<env>/secret-key      — Application secret key
```

## How to Deploy

### Staging (Automatic)

Staging deploys automatically when code is merged to `main`:

1. Open a pull request to `main`.
2. CI pipeline runs: lint, type-check, tests, security scan, Docker build.
3. On merge, the staging pipeline triggers:
   - Builds and pushes Docker images to ECR
   - Updates ECS task definitions with new image tags
   - Deploys API, Frontend, Worker, and Beat services
   - Runs E2E tests against staging
   - Sends Slack notification

### Production (Tag-based)

Production deploys on version tag push:

```bash
# 1. Ensure main is up to date and staging is verified
git checkout main
git pull origin main

# 2. Create a version tag
git tag -a v1.2.3 -m "Release v1.2.3: description of changes"

# 3. Push the tag to trigger production deployment
git push origin v1.2.3
```

The production pipeline:
- Builds and pushes images tagged with the version
- Saves current task definitions for rollback
- Performs blue-green deployment via CodeDeploy
- Runs health checks after stabilization
- Auto-rollbacks if error rate exceeds 1%
- Sends Slack notification

### Manual Deployment

Use the deploy script for manual deployments:

```bash
# Deploy to staging
make deploy-staging

# Deploy specific version to production
make deploy-prod TAG=v1.2.3

# Or use the script directly
bash infra/scripts/deploy.sh staging v1.2.3
bash infra/scripts/deploy.sh production v1.2.3
```

Required environment variables for manual deployment:

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=123456789012
export HEALTH_CHECK_URL=https://staging.selfpublisherforge.com/api/health
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## How to Rollback

### Automatic Rollback

The production pipeline automatically rolls back if:
- Health check endpoint returns non-200 status
- 5xx error rate exceeds 1% within 5 minutes of deployment
- ECS service fails to stabilize

### Manual Rollback

```bash
# Rollback staging
make rollback-staging

# Rollback production
make rollback-prod

# Or use the script directly
bash infra/scripts/deploy.sh rollback staging
bash infra/scripts/deploy.sh rollback production
```

### Emergency Rollback via AWS Console

1. Go to **ECS > Clusters > selfpublisherforge-production**
2. Select the service (e.g., `selfpublisherforge-api-production`)
3. Click **Update**
4. Under Task Definition, select the previous revision
5. Click **Update Service**
6. Repeat for all services (api, frontend, worker, beat)

## Infrastructure Management

### Terraform

```bash
# Initialize Terraform (first time or after provider changes)
make tf-init

# Preview changes for staging
make tf-plan ENV=staging

# Apply changes to staging
make tf-apply ENV=staging

# Preview changes for production
make tf-plan ENV=production

# Apply changes to production (requires approval)
make tf-apply ENV=production
```

### Terraform State

- State is stored in S3: `s3://selfpublisherforge-terraform-state/infra/terraform.tfstate`
- State locking uses DynamoDB: `selfpublisherforge-terraform-locks`
- Never manually edit state files; use `terraform state` commands

## Monitoring

### Dashboards

- **Datadog Dashboard**: Imported from `infra/monitoring/datadog-dashboard.json`
  - API latency (P50/P95/P99)
  - Error rates and response code distribution
  - Celery queue depth and task throughput
  - Database connections, CPU, and IOPS
  - Redis memory and cache hit rates
  - ECS CPU and memory utilization per service

### Alerts

Alert definitions are in `infra/monitoring/alerts.yml`. Severity tiers:

| Tier | Response Time | Examples | Notification |
|---|---|---|---|
| **P0** | Immediate | Service down, DB failure, >5% errors | PagerDuty critical + Slack |
| **P1** | 15 minutes | >1% errors, P95 >2s, queue >500, RDS CPU >90% | PagerDuty high + Slack |
| **P2** | 1 hour | Task restarts, P95 >500ms, low storage | Slack alerts |
| **P3** | Next business day | Sustained high CPU, low cache hit rate | Slack monitoring |

### Log Access

```bash
# Tail API logs
make logs SERVICE=api

# View logs in CloudWatch
aws logs tail /ecs/selfpublisherforge-api-production --follow

# Search for errors in the last hour
aws logs filter-log-events \
  --log-group-name /ecs/selfpublisherforge-api-production \
  --start-time $(date -d '1 hour ago' +%s000) \
  --filter-pattern "ERROR"
```

### Key Health Endpoints

| Endpoint | Purpose |
|---|---|
| `/api/health` | API health check (used by ALB and deployment pipeline) |
| `localhost:5555` | Flower (Celery monitoring, dev only) |

## Common Operations

### Scaling

```bash
# Scale API service
aws ecs update-service \
  --cluster selfpublisherforge-production \
  --service selfpublisherforge-api-production \
  --desired-count 5

# Auto-scaling is configured for the API service (2-10 instances)
# Scales on CPU (>70%) and memory (>80%) utilization
```

### Database

```bash
# Run migrations
make migrate

# Create new migration
make migrate-create MSG="add new column"

# Rollback one migration
make migrate-rollback

# Connect to production DB (via bastion/SSM)
aws ssm start-session --target <bastion-instance-id>
psql "postgresql://spf_admin@<rds-endpoint>:5432/selfpublisherforge"
```

### Secrets Rotation

```bash
# Update a secret in SSM Parameter Store
aws ssm put-parameter \
  --name "/selfpublisherforge/production/secret-key" \
  --value "NEW_SECRET_VALUE" \
  --type SecureString \
  --overwrite

# Force service restart to pick up new secrets
aws ecs update-service \
  --cluster selfpublisherforge-production \
  --service selfpublisherforge-api-production \
  --force-new-deployment
```

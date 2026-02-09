# W12: DevOps — Docker, CI/CD, Terraform, Monitoring
**Branch:** `ai-feature/devops-infrastructure`
**Scope:** infra

## Mission
Set up production-ready DevOps: multi-stage Dockerfiles, GitHub Actions CI/CD pipeline, Terraform infrastructure-as-code for AWS, and monitoring/alerting configuration.

## What to Build

### Docker
1. **backend/Dockerfile** — REPLACE with multi-stage: build stage (install deps) + runtime stage (slim image, non-root user)
2. **frontend/Dockerfile** — REPLACE with multi-stage: deps stage + build stage + runtime stage (standalone output)
3. **backend/Dockerfile.dev** — Development Dockerfile with hot reload
4. **frontend/Dockerfile.dev** — Development Dockerfile with hot reload

### CI/CD (GitHub Actions)
5. **.github/workflows/ci.yml** — On PR:
   - Lint (ruff for Python, eslint for TS)
   - Type check (mypy, tsc)
   - Unit tests (pytest, jest) with coverage
   - Integration tests
   - Build Docker images
   - Security scan (pip-audit, npm audit)

6. **.github/workflows/deploy-staging.yml** — On merge to main:
   - Build and push Docker images to ECR
   - Deploy to staging ECS
   - Run E2E tests against staging
   - Notify Slack

7. **.github/workflows/deploy-production.yml** — On tag push:
   - Blue-green deployment to production ECS
   - Health checks
   - Auto-rollback if error rate > 1%
   - Notify Slack

### Terraform
8. **infra/terraform/main.tf** — Provider config, backend (S3 state), variables
9. **infra/terraform/ecs.tf** — ECS cluster, task definitions, services (api, worker, beat)
10. **infra/terraform/rds.tf** — PostgreSQL RDS instance, security group, parameter group
11. **infra/terraform/elasticache.tf** — Redis ElastiCache cluster
12. **infra/terraform/s3.tf** — S3 buckets for assets and backups
13. **infra/terraform/networking.tf** — VPC, subnets, security groups, ALB
14. **infra/terraform/variables.tf** — All configurable variables with defaults
15. **infra/terraform/outputs.tf** — Key outputs (ALB URL, RDS endpoint, etc.)

### Monitoring
16. **infra/monitoring/datadog-dashboard.json** — Dashboard definition: API latency, error rates, queue depth, DB connections
17. **infra/monitoring/alerts.yml** — Alert definitions matching blueprint severity tiers (P0-P3)

### Scripts
18. **infra/scripts/deploy.sh** — Deployment script with rollback capability
19. **Makefile** — Common commands: dev, build, test, lint, migrate, deploy-staging, deploy-prod

### Docs
20. **docs/deploy.md** — Deployment guide: environments, how to deploy, how to rollback, monitoring

## Commit Convention
`feat(devops): implement CI/CD pipeline, Terraform IaC, and monitoring configuration`

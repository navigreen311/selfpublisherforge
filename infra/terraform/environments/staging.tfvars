# =============================================================================
# Staging Environment — Terraform variable overrides
# =============================================================================
#
# This file configures a cost-effective staging environment for testing and
# development. Instance sizes are smaller than production, and access is open
# to simplify testing workflows.
#
# CHECKLIST — complete every item before running terraform apply:
#
#   [ ] 1. Export the four required secret environment variables (see Secrets section)
#   [ ] 2. (Optional) Set domain_name if you have a staging subdomain
#   [ ] 3. (Optional) Set certificate_arn if using HTTPS in staging
#   [ ] 4. (Optional) Set alarm_sns_topic_arn for staging alerts
#
# HOW TO DEPLOY:
#   1. Export the four required environment variables (see "Secrets" section).
#   2. Optionally fill in domain_name and certificate_arn if using a custom domain.
#   3. Run:  terraform plan  -var-file=environments/staging.tfvars
#   4. Run:  terraform apply -var-file=environments/staging.tfvars
# =============================================================================

environment = "staging"
aws_region  = "us-east-1"

# =============================================================================
# Networking
# =============================================================================
vpc_cidr                 = "10.1.0.0/16"   # Different CIDR from production (10.0.0.0/16) to allow VPC peering
availability_zones_count = 2

# Staging — open for testing. Restrict in production.
allowed_cidr_blocks = ["0.0.0.0/0"]

# =============================================================================
# ECS — Smaller containers suitable for staging workloads
# =============================================================================
# CPU units:  256 = 0.25 vCPU, 512 = 0.5 vCPU, 1024 = 1 vCPU
# Memory:     MiB — must be compatible with the CPU value (see AWS Fargate docs)

# --- API service (Django / DRF backend) ---
api_cpu            = 256    # 0.25 vCPU (half of production)
api_memory         = 512    # 512 MB
api_desired_count  = 1      # single instance is sufficient for staging
api_min_count      = 1      # auto-scaling floor
api_max_count      = 3      # auto-scaling ceiling

# --- Frontend service (Next.js / static serving) ---
frontend_cpu           = 256
frontend_memory        = 512
frontend_desired_count = 1

# --- Celery worker (async task processing) ---
worker_cpu           = 256
worker_memory        = 512
worker_desired_count = 1

# --- Celery beat (periodic task scheduler — only ever 1 instance) ---
beat_cpu    = 256
beat_memory = 256

# =============================================================================
# RDS — PostgreSQL staging database (smaller, single-AZ)
# =============================================================================
db_instance_class        = "db.t3.small"   # 1 vCPU, 2 GB RAM (production: db.t3.medium)
db_allocated_storage     = 20              # initial storage in GB (production: 50)
db_max_allocated_storage = 50              # auto-scaling upper limit (production: 200)
db_name                  = "selfpublisherforge"
db_multi_az              = false           # single-AZ is fine for staging (saves cost)
db_backup_retention      = 3              # fewer backup days for staging (production: 7)

# ---------------------------------------------------------------------------
# Secrets — NEVER put actual values in this file.
# Set each one as a shell environment variable before running terraform.
#
#   export TF_VAR_db_username="staging_admin"
#     - The master username for the staging RDS instance.
#     - Can differ from production. Example: "spf_staging_admin"
#
#   export TF_VAR_db_password="$(openssl rand -base64 24)"
#     - The master password for the staging RDS instance.
#     - Requirements: at least 16 characters, mix of upper/lower/digits/symbols.
#
#   export TF_VAR_jwt_secret_key="$(openssl rand -hex 32)"
#     - JWT signing secret for the staging API.
#     - MUST differ from production for security isolation.
#
#   export TF_VAR_app_secret_key="$(openssl rand -hex 50)"
#     - Django SECRET_KEY for the staging environment.
#     - MUST differ from production for security isolation.
# ---------------------------------------------------------------------------

# =============================================================================
# ElastiCache — Redis (smaller node for staging)
# =============================================================================
redis_node_type       = "cache.t3.micro"   # 0.5 GB memory (production: cache.t3.medium)
redis_num_cache_nodes = 1
redis_engine_version  = "7.1"

# =============================================================================
# S3 — Bucket names with "-staging" suffix
# =============================================================================
# S3 bucket names must be globally unique. The "-staging" suffix prevents
# collisions with production buckets in the same AWS account.
assets_bucket_name   = "selfpublisherforge-assets-staging"
backups_bucket_name  = "selfpublisherforge-backups-staging"
frontend_bucket_name = "selfpublisherforge-frontend-staging"

# =============================================================================
# Logging
# =============================================================================
log_retention_days      = 14   # shorter retention for staging (production: 30)
flow_log_retention_days = 7    # shorter retention for staging (production: 14)

# =============================================================================
# WAF — More permissive rate limit for testing
# =============================================================================
waf_rate_limit = 5000   # requests per 5-min per IP (production: 2000) — permissive for load testing

# =============================================================================
# Domain & SSL/TLS (Optional for staging)
# =============================================================================
#
# If you have a staging subdomain (e.g., "staging.selfpublisherforge.com"),
# set these values. Otherwise, leave them empty and access staging via
# the ALB DNS name directly.
#
# To set up a staging domain:
#   1. Request an ACM certificate (see production.tfvars for step-by-step).
#   2. Point your staging DNS record to the ALB DNS name output by Terraform.
#
# >>> TODO (Optional): Set staging domain and certificate <<<
domain_name     = ""   # TODO (Optional): e.g., "staging.selfpublisherforge.com"
certificate_arn = ""   # TODO (Optional): e.g., "arn:aws:acm:us-east-1:123456789012:certificate/<UUID>"

# =============================================================================
# Monitoring & Alerting (Optional for staging)
# =============================================================================
#
# Setting this in staging is optional but recommended for early warning of
# issues in your pre-production environment.
#
# To create a staging SNS topic:
#   aws sns create-topic --name selfpublisherforge-staging-alarms --region us-east-1
#   aws sns subscribe --topic-arn <TopicArn> --protocol email \
#     --notification-endpoint your-email@example.com --region us-east-1
#
# >>> TODO (Optional): Set SNS topic ARN for staging alerts <<<
alarm_sns_topic_arn = ""   # TODO (Optional): e.g., "arn:aws:sns:us-east-1:123456789012:selfpublisherforge-staging-alarms"

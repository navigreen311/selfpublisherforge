# =============================================================================
# Staging Environment — Terraform variable overrides
# =============================================================================
#
# Staging uses smaller, cost-efficient resource sizes for development and
# testing. Most values are pre-configured; you only need to set the four
# secret environment variables before deploying.
#
# REQUIRED environment variables (set before running terraform):
#   - TF_VAR_db_password   (database master password)
#   - TF_VAR_db_username   (database master username)
#   - TF_VAR_jwt_secret_key (JWT signing secret)
#   - TF_VAR_app_secret_key (Django SECRET_KEY)
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
#
# allowed_cidr_blocks — CIDR blocks permitted to reach the ALB.
# This is REQUIRED (Terraform validation will fail if empty).
#
# For staging, you might restrict access to your office/VPN IP to prevent
# public exposure, or use "0.0.0.0/0" if the staging site should be
# publicly accessible.
#
# Examples:
#   allowed_cidr_blocks = ["0.0.0.0/0"]                  # open to everyone
#   allowed_cidr_blocks = ["203.0.113.0/24"]              # single office range
#   allowed_cidr_blocks = ["10.0.0.0/8", "172.16.0.0/12"] # internal ranges
#
allowed_cidr_blocks = ["0.0.0.0/0"]   # open access for staging — restrict for sensitive workloads

# vpc_cidr — CIDR block for the staging VPC.
# Default: "10.0.0.0/16" (defined in variables.tf). Override only if you
# need to avoid CIDR conflicts with peered VPCs or VPN tunnels.
# vpc_cidr = "10.0.0.0/16"

# availability_zones_count — Number of AZs to spread resources across.
# Default: 2 (defined in variables.tf). Two is a good minimum for ALB.
# availability_zones_count = 2

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

# --- Frontend service ---
frontend_cpu       = 256
frontend_memory    = 512
frontend_desired_count = 1

# --- Celery worker ---
worker_cpu         = 256
worker_memory      = 512
worker_desired_count = 1

# --- Celery beat ---
beat_cpu           = 256
beat_memory        = 256

# =============================================================================
# RDS — PostgreSQL staging database (smaller, single-AZ)
# =============================================================================
db_instance_class        = "db.t3.small"   # 2 vCPU, 2 GB RAM
db_allocated_storage     = 20              # initial storage in GB
db_max_allocated_storage = 50              # auto-scaling upper limit in GB
db_multi_az              = false           # single-AZ is fine for staging (saves cost)
db_backup_retention      = 3              # fewer backup days for staging

# db_name — Name of the PostgreSQL database created on the RDS instance.
# Default: "selfpublisherforge" (defined in variables.tf).
# Override if you want a different DB name in staging, e.g., to run
# multiple staging environments against the same account.
# db_name = "selfpublisherforge_staging"

# ---------------------------------------------------------------------------
# Secrets — NEVER put actual values in this file.
# Set each one as a shell environment variable before running terraform.
#
#   export TF_VAR_db_username="your_staging_db_username"
#     - The master username for the staging RDS instance.
#     - Can differ from production. Example: "spf_staging_admin"
#
#   export TF_VAR_db_password="your_staging_db_password"
#     - The master password for the staging RDS instance.
#     - Generate one:  openssl rand -base64 24
#
#   export TF_VAR_jwt_secret_key="your_staging_jwt_key"
#     - JWT signing secret for the staging API.
#     - MUST differ from production for security isolation.
#     - Generate one:  openssl rand -hex 32
#
#   export TF_VAR_app_secret_key="your_staging_django_key"
#     - Django SECRET_KEY for the staging environment.
#     - MUST differ from production for security isolation.
#     - Generate one:  openssl rand -hex 50
# ---------------------------------------------------------------------------

# =============================================================================
# ElastiCache — Redis (smaller node for staging)
# =============================================================================
redis_node_type       = "cache.t3.small"   # 1.37 GB memory
redis_num_cache_nodes = 1

# redis_engine_version — Redis engine version.
# Default: "7.1" (defined in variables.tf). Override only if you need to
# test against a specific Redis version before upgrading production.
# redis_engine_version = "7.1"

# =============================================================================
# S3 Buckets
# =============================================================================
#
# S3 bucket names must be globally unique. The defaults in variables.tf
# do NOT include an environment suffix, so you SHOULD override them for
# staging to avoid collisions with production buckets.
#
# Recommended pattern: "<project>-<purpose>-staging"
#
# assets_bucket_name — Stores user-uploaded assets (book covers, PDFs, etc.)
# assets_bucket_name = "selfpublisherforge-assets-staging"
#
# backups_bucket_name — Stores automated database backups.
# backups_bucket_name = "selfpublisherforge-backups-staging"
#
# frontend_bucket_name — Stores the Next.js static build output served by CloudFront.
# frontend_bucket_name = "selfpublisherforge-frontend-staging"

# =============================================================================
# Logging
# =============================================================================
log_retention_days = 14   # shorter retention for staging (saves cost)

# flow_log_retention_days — Retention for VPC Flow Logs in CloudWatch.
# Default: 14 days (defined in variables.tf). Flow logs help diagnose
# network connectivity issues. Reduce to 7 days if cost is a concern.
# flow_log_retention_days = 7

# =============================================================================
# WAF — Web Application Firewall
# =============================================================================
#
# waf_rate_limit — Max requests per 5-minute window per IP before WAF blocks.
# Default: 2000 (defined in variables.tf).
# A lower limit in staging can help catch runaway scripts or load tests
# that accidentally target the wrong environment.
# waf_rate_limit = 1000

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
#   2. Point your staging DNS record (e.g., staging.selfpublisherforge.com)
#      to the ALB DNS name output by Terraform.
#
# If left empty, HTTPS will not be configured on the ALB/CloudFront
# and the service will be available on the ALB's default DNS.
#
# domain_name — The staging domain name used for ALB listener rules,
#   CloudFront, and Route 53. Leave empty ("") to skip custom domain setup.
#   Example: "staging.selfpublisherforge.com"
#
# certificate_arn — ARN of the ACM certificate covering the staging domain.
#   Must be in us-east-1 (required by CloudFront). Leave empty ("") if not
#   using a custom domain.
#   Example: "arn:aws:acm:us-east-1:123456789012:certificate/abcd-1234-efgh-5678"
#
domain_name     = ""   # TODO: (Optional) Set to staging domain, e.g., "staging.selfpublisherforge.com"
certificate_arn = ""   # TODO: (Optional) Set to ACM certificate ARN if using a custom staging domain

# =============================================================================
# Monitoring & Alerting (Optional for staging)
# =============================================================================
#
# alarm_sns_topic_arn — ARN of the SNS topic that receives CloudWatch Alarm
#   notifications (CPU spikes, unhealthy targets, high error rates, etc.).
#   Default: "" (alarms created but have no notification target).
#
#   Setting this in staging is optional but recommended if you want early
#   warning of issues in your pre-production environment.
#
#   To create a staging SNS topic:
#     aws sns create-topic --name selfpublisherforge-staging-alarms --region us-east-1
#     aws sns subscribe --topic-arn <TopicArn> --protocol email \
#       --notification-endpoint your-email@example.com --region us-east-1
#
# alarm_sns_topic_arn = "arn:aws:sns:us-east-1:123456789012:selfpublisherforge-staging-alarms"

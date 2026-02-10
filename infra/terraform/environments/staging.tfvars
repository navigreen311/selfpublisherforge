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

# =============================================================================
# Logging
# =============================================================================
log_retention_days = 14   # shorter retention for staging (saves cost)

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
domain_name     = ""   # TODO: (Optional) Set to staging domain, e.g., "staging.selfpublisherforge.com"
certificate_arn = ""   # TODO: (Optional) Set to ACM certificate ARN if using a custom staging domain

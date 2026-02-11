# =============================================================================
# Production Environment — Terraform variable overrides
# =============================================================================
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!  WARNING: THIS FILE CONTAINS PLACEHOLDER VALUES THAT MUST BE          !!!
# !!!  REPLACED BEFORE YOUR FIRST PRODUCTION DEPLOYMENT.                    !!!
# !!!                                                                       !!!
# !!!  Search for "TODO" to find every value that needs your attention.     !!!
# !!!  Terraform validation will BLOCK deployment if placeholders remain.   !!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
# CHECKLIST — complete every item before running terraform apply:
#
#   [ ] 1. Replace domain_name with your actual production domain
#   [ ] 2. Replace certificate_arn with your real ACM certificate ARN
#          (must NOT contain "YOUR_AWS_ACCOUNT_ID" or "REPLACE_ME")
#   [ ] 3. Replace alarm_sns_topic_arn with your real SNS topic ARN
#          (must NOT contain "YOUR_AWS_ACCOUNT_ID")
#   [ ] 4. Replace allowed_cidr_blocks with your actual IP ranges
#          (or ["0.0.0.0/0"] if the app is public-facing)
#   [ ] 5. Replace S3 bucket name suffixes with your AWS account ID
#   [ ] 6. Export the four required secret environment variables:
#            export TF_VAR_db_username="..."
#            export TF_VAR_db_password="..."
#            export TF_VAR_jwt_secret_key="..."
#            export TF_VAR_app_secret_key="..."
#
# HOW TO DEPLOY:
#   1. Complete all TODO items below (replace every placeholder).
#   2. Export the four required environment variables (see "Secrets" section).
#   3. Run:  terraform plan  -var-file=environments/production.tfvars
#   4. Run:  terraform apply -var-file=environments/production.tfvars
# =============================================================================

environment = "production"
aws_region  = "us-east-1"

# =============================================================================
# Networking
# =============================================================================
vpc_cidr                 = "10.0.0.0/16"
availability_zones_count = 2

# ---------------------------------------------------------------------------
# Allowed CIDR Blocks — Controls who can reach the ALB
# ---------------------------------------------------------------------------
# SECURITY: For a public-facing web app, use ["0.0.0.0/0"].
# For internal/restricted apps, list specific IP ranges (office, VPN, etc.).
#
# >>> TODO: Replace with your actual allowed CIDR ranges <<<
# Examples:
#   ["0.0.0.0/0"]                           — public-facing app (open to all)
#   ["203.0.113.0/24", "198.51.100.0/24"]   — office + VPN only
allowed_cidr_blocks = ["0.0.0.0/0"]   # TODO: Review — restrict if app is not public-facing

# =============================================================================
# ECS — Container sizing for production workloads
# =============================================================================
# CPU units:  256 = 0.25 vCPU, 512 = 0.5 vCPU, 1024 = 1 vCPU
# Memory:     MiB — must be compatible with the CPU value (see AWS Fargate docs)

# --- API service (Django / DRF backend) ---
api_cpu            = 512    # 0.5 vCPU
api_memory         = 1024   # 1 GB
api_desired_count  = 2      # baseline running tasks
api_min_count      = 2      # auto-scaling floor
api_max_count      = 10     # auto-scaling ceiling

# --- Frontend service (Next.js / static serving) ---
frontend_cpu           = 256    # 0.25 vCPU
frontend_memory        = 512    # 512 MB
frontend_desired_count = 2

# --- Celery worker (async task processing) ---
worker_cpu           = 512
worker_memory        = 1024
worker_desired_count = 2

# --- Celery beat (periodic task scheduler — only ever 1 instance) ---
beat_cpu    = 256
beat_memory = 512

# =============================================================================
# RDS — PostgreSQL production database
# =============================================================================
db_instance_class        = "db.t3.medium"   # 2 vCPU, 4 GB RAM
db_allocated_storage     = 50               # initial storage in GB
db_max_allocated_storage = 200              # auto-scaling upper limit in GB
db_name                  = "selfpublisherforge"
db_multi_az              = true             # REQUIRED for production HA
db_backup_retention      = 7               # days to retain automated backups

# ---------------------------------------------------------------------------
# Secrets — NEVER put actual values in this file.
# Set each one as a shell environment variable before running terraform.
#
#   export TF_VAR_db_username="your_db_master_username"
#     - The master username for the RDS PostgreSQL instance.
#     - Choose something other than "postgres" for security.
#     - Example: "spf_admin"
#
#   export TF_VAR_db_password="your_db_master_password"
#     - The master password for the RDS PostgreSQL instance.
#     - Requirements: at least 16 characters, mix of upper/lower/digits/symbols.
#     - Generate one:  openssl rand -base64 24
#
#   export TF_VAR_jwt_secret_key="your_jwt_signing_key"
#     - Used by the API to sign and verify JSON Web Tokens.
#     - Generate one:  openssl rand -hex 32
#
#   export TF_VAR_app_secret_key="your_django_secret_key"
#     - The Django SECRET_KEY for cryptographic signing.
#     - Generate one:  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
#     - Or:  openssl rand -hex 50
# ---------------------------------------------------------------------------

# =============================================================================
# ElastiCache — Redis for caching and Celery broker
# =============================================================================
redis_node_type       = "cache.t3.medium"   # 3.09 GB memory
redis_num_cache_nodes = 1
redis_engine_version  = "7.1"

# =============================================================================
# S3 — Bucket names with account-specific suffix for global uniqueness
# =============================================================================
# S3 bucket names must be globally unique across all AWS accounts. Using your
# AWS account ID as a suffix guarantees uniqueness and clearly ties buckets
# to your account.
#
# >>> TODO: Replace YOUR_AWS_ACCOUNT_ID with your 12-digit AWS account ID <<<
# To find your account ID:  aws sts get-caller-identity --query Account --output text
assets_bucket_name   = "selfpublisherforge-assets-YOUR_AWS_ACCOUNT_ID"     # TODO: Replace YOUR_AWS_ACCOUNT_ID
backups_bucket_name  = "selfpublisherforge-backups-YOUR_AWS_ACCOUNT_ID"    # TODO: Replace YOUR_AWS_ACCOUNT_ID
frontend_bucket_name = "selfpublisherforge-frontend-YOUR_AWS_ACCOUNT_ID"   # TODO: Replace YOUR_AWS_ACCOUNT_ID

# =============================================================================
# Logging
# =============================================================================
log_retention_days      = 30   # CloudWatch log retention in days
flow_log_retention_days = 14   # VPC Flow Logs retention in days

# =============================================================================
# WAF — Web Application Firewall
# =============================================================================
waf_rate_limit = 2000   # requests per 5-min per IP — tune based on expected traffic

# =============================================================================
# Domain & SSL/TLS
# =============================================================================
#
# REQUIRED: Your production domain name.
# This is used for the ALB listener rules, CloudFront distribution, and Route 53.
# Example: "selfpublisherforge.com"
#
# >>> TODO: Replace with your actual production domain <<<
# Terraform will NOT block on this value, but ensure it matches the domain
# you used when requesting your ACM certificate.
domain_name = "selfpublisherforge.com"

# ---------------------------------------------------------------------------
# ACM Certificate ARN
# ---------------------------------------------------------------------------
# REQUIRED for HTTPS on the ALB and CloudFront.
#
# HOW TO OBTAIN THE ACM CERTIFICATE ARN — step by step:
#
#   Step 1: Request a certificate in us-east-1 (required for CloudFront):
#     aws acm request-certificate \
#       --domain-name selfpublisherforge.com \
#       --subject-alternative-names "*.selfpublisherforge.com" \
#       --validation-method DNS \
#       --region us-east-1
#
#   Step 2: The command returns a CertificateArn. Note it down.
#
#   Step 3: Get the DNS validation records:
#     aws acm describe-certificate \
#       --certificate-arn <CertificateArn> \
#       --region us-east-1 \
#       --query 'Certificate.DomainValidationOptions[].ResourceRecord'
#
#   Step 4: Create the CNAME record(s) in your DNS provider (Route 53,
#           Cloudflare, etc.) using the Name and Value from Step 3.
#
#   Step 5: Wait for validation (can take 5-30 minutes):
#     aws acm wait certificate-validated \
#       --certificate-arn <CertificateArn> \
#       --region us-east-1
#
#   Step 6: Paste the ARN below.
#
# Format: arn:aws:acm:us-east-1:<ACCOUNT_ID>:certificate/<UUID>
#
# >>> TODO: Replace with your real ACM certificate ARN <<<
# Deployment will FAIL if this still contains "YOUR_AWS_ACCOUNT_ID" or "REPLACE_ME".
certificate_arn = "arn:aws:acm:us-east-1:YOUR_AWS_ACCOUNT_ID:certificate/REPLACE_ME"

# =============================================================================
# Monitoring & Alerting
# =============================================================================
#
# SNS Topic ARN — used by CloudWatch Alarms to send notifications.
#
# HOW TO CREATE THE SNS TOPIC — step by step:
#
#   Step 1: Create the topic:
#     aws sns create-topic --name selfpublisherforge-production-alarms --region us-east-1
#
#     The command returns a TopicArn. Note it down.
#
#   Step 2: Subscribe your email to the topic:
#     aws sns subscribe \
#       --topic-arn <TopicArn> \
#       --protocol email \
#       --notification-endpoint your-email@example.com \
#       --region us-east-1
#
#   Step 3: Check your inbox and confirm the subscription by clicking the
#           confirmation link in the email from AWS.
#
#   Step 4: (Optional) Add a PagerDuty / Slack / OpsGenie integration:
#     aws sns subscribe \
#       --topic-arn <TopicArn> \
#       --protocol https \
#       --notification-endpoint https://events.pagerduty.com/integration/<key>/enqueue
#
#   Step 5: Paste the TopicArn below.
#
# Format: arn:aws:sns:us-east-1:<ACCOUNT_ID>:selfpublisherforge-production-alarms
#
# >>> TODO: Replace with your real SNS topic ARN <<<
# Deployment will FAIL if this still contains "YOUR_AWS_ACCOUNT_ID".
alarm_sns_topic_arn = "arn:aws:sns:us-east-1:YOUR_AWS_ACCOUNT_ID:selfpublisherforge-alarms"

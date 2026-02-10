# =============================================================================
# Production Environment — Terraform variable overrides
# =============================================================================
#
# VALIDATION: Before applying this configuration, ensure the following
# required values are set:
#   - domain_name       (must not be empty)
#   - certificate_arn   (must not be empty)
#   - alarm_sns_topic_arn (must not be empty)
#   - TF_VAR_db_password, TF_VAR_db_username, TF_VAR_jwt_secret_key,
#     TF_VAR_app_secret_key must be set as environment variables.
# =============================================================================

environment = "production"
aws_region  = "us-east-1"

# ECS — production-sized instances
api_cpu            = 512
api_memory         = 1024
api_desired_count  = 2
api_min_count      = 2
api_max_count      = 10
frontend_cpu       = 256
frontend_memory    = 512
frontend_desired_count = 2
worker_cpu         = 512
worker_memory      = 1024
worker_desired_count = 2
beat_cpu           = 256
beat_memory        = 512

# RDS — production-grade
db_instance_class        = "db.t3.medium"
db_allocated_storage     = 50
db_max_allocated_storage = 200
db_multi_az              = true
db_backup_retention      = 7
# db_password      - SET VIA TF_VAR_db_password ENVIRONMENT VARIABLE — never commit secrets
# db_username      - SET VIA TF_VAR_db_username ENVIRONMENT VARIABLE — never commit secrets
# jwt_secret_key   - SET VIA TF_VAR_jwt_secret_key ENVIRONMENT VARIABLE — never commit secrets
# app_secret_key   - SET VIA TF_VAR_app_secret_key ENVIRONMENT VARIABLE — never commit secrets

# Redis — production-grade
redis_node_type       = "cache.t3.medium"
redis_num_cache_nodes = 1

# Logging
log_retention_days = 30

# Domain — MUST be set before production deployment
domain_name     = ""  # REQUIRED: Set to your domain (e.g., "app.selfpublisherforge.com")
certificate_arn = ""  # REQUIRED: Set to your ACM certificate ARN (e.g., "arn:aws:acm:us-east-1:123456789012:certificate/abcd-1234")

# Monitoring
alarm_sns_topic_arn = ""  # REQUIRED: Set to your SNS topic ARN for CloudWatch alarms

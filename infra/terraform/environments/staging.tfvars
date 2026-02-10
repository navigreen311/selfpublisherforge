# =============================================================================
# Staging Environment — Terraform variable overrides
# =============================================================================

environment = "staging"
aws_region  = "us-east-1"

# ECS — smaller instances for staging
api_cpu            = 256
api_memory         = 512
api_desired_count  = 1
api_min_count      = 1
api_max_count      = 3
frontend_cpu       = 256
frontend_memory    = 512
frontend_desired_count = 1
worker_cpu         = 256
worker_memory      = 512
worker_desired_count = 1
beat_cpu           = 256
beat_memory        = 256

# RDS — smaller instance for staging
db_instance_class       = "db.t3.small"
db_allocated_storage    = 20
db_max_allocated_storage = 50
db_multi_az             = false
db_backup_retention     = 3
# db_password      - SET VIA TF_VAR_db_password ENVIRONMENT VARIABLE — never commit secrets
# db_username      - SET VIA TF_VAR_db_username ENVIRONMENT VARIABLE — never commit secrets
# jwt_secret_key   - SET VIA TF_VAR_jwt_secret_key ENVIRONMENT VARIABLE — never commit secrets
# app_secret_key   - SET VIA TF_VAR_app_secret_key ENVIRONMENT VARIABLE — never commit secrets

# Redis — smaller instance for staging
redis_node_type       = "cache.t3.small"
redis_num_cache_nodes = 1

# Logging
log_retention_days = 14

# Domain (set to actual staging domain when available)
# Optional for staging - set if you have a staging domain
domain_name     = ""
# Optional for staging - set if using custom domain with HTTPS
certificate_arn = ""

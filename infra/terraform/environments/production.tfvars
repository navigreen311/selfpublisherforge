# =============================================================================
# Production Environment — Terraform variable overrides
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

# Domain (set to actual production domain)
domain_name     = ""
certificate_arn = ""

# Monitoring
alarm_sns_topic_arn = ""

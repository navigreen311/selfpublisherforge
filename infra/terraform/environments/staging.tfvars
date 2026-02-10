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
db_password             = "CHANGE_ME_STAGING_PASSWORD"

# Redis — smaller instance for staging
redis_node_type       = "cache.t3.small"
redis_num_cache_nodes = 1

# Logging
log_retention_days = 14

# Domain (set to actual staging domain when available)
domain_name     = ""
certificate_arn = ""

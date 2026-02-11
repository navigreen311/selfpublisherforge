# =============================================================================
# Terraform Variables — All configurable parameters with sensible defaults
# =============================================================================

# -----------------------------------------------------------------------------
# General
# -----------------------------------------------------------------------------
variable "project_name" {
  description = "Name of the project, used as prefix for all resources"
  type        = string
  default     = "selfpublisherforge"
}

variable "environment" {
  description = "Deployment environment (staging, production)"
  type        = string
  default     = "staging"
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be 'staging' or 'production'."
  }
}

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

# -----------------------------------------------------------------------------
# Networking
# -----------------------------------------------------------------------------
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones_count" {
  description = "Number of availability zones to use"
  type        = number
  default     = 2
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the ALB — MUST be explicitly configured for production (no default access)"
  type        = list(string)
  default     = []

  # Empty list means no SSH/direct access allowed. Set explicitly for your environment.
  #
  # SECURITY NOTE: If this list contains "0.0.0.0/0", the ALB will be open to
  # the entire internet. This is acceptable for staging/public-facing sites but
  # should be reviewed carefully for production. Consider restricting to known
  # IP ranges (e.g., office IPs, VPN CIDR) if the application is not public.

  validation {
    condition = alltrue([
      for cidr in var.allowed_cidr_blocks :
      can(cidrhost(cidr, 0))
    ])
    error_message = "Each entry in allowed_cidr_blocks must be a valid CIDR block (e.g., '10.0.0.0/16' or '0.0.0.0/0')."
  }
}

# -----------------------------------------------------------------------------
# ECS
# -----------------------------------------------------------------------------
variable "api_cpu" {
  description = "CPU units for the API task (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "api_memory" {
  description = "Memory (MiB) for the API task"
  type        = number
  default     = 1024
}

variable "api_desired_count" {
  description = "Desired number of API task instances"
  type        = number
  default     = 2
}

variable "api_min_count" {
  description = "Minimum number of API task instances for auto-scaling"
  type        = number
  default     = 2
}

variable "api_max_count" {
  description = "Maximum number of API task instances for auto-scaling"
  type        = number
  default     = 10
}

variable "frontend_cpu" {
  description = "CPU units for the Frontend task"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Memory (MiB) for the Frontend task"
  type        = number
  default     = 512
}

variable "frontend_desired_count" {
  description = "Desired number of Frontend task instances"
  type        = number
  default     = 2
}

variable "worker_cpu" {
  description = "CPU units for the Celery worker task"
  type        = number
  default     = 512
}

variable "worker_memory" {
  description = "Memory (MiB) for the Celery worker task"
  type        = number
  default     = 1024
}

variable "worker_desired_count" {
  description = "Desired number of Celery worker instances"
  type        = number
  default     = 2
}

variable "beat_cpu" {
  description = "CPU units for the Celery beat task"
  type        = number
  default     = 256
}

variable "beat_memory" {
  description = "Memory (MiB) for the Celery beat task"
  type        = number
  default     = 512
}

# -----------------------------------------------------------------------------
# RDS (PostgreSQL)
# -----------------------------------------------------------------------------
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS (GB)"
  type        = number
  default     = 50
}

variable "db_max_allocated_storage" {
  description = "Maximum storage for RDS auto-scaling (GB)"
  type        = number
  default     = 200
}

variable "db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "selfpublisherforge"
}

variable "db_username" {
  description = "Master username for the RDS instance"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Master password for the RDS instance — pass via TF_VAR_db_password env variable"
  type        = string
  sensitive   = true
}

variable "db_multi_az" {
  description = "Enable Multi-AZ deployment for RDS"
  type        = bool
  default     = false
}

variable "db_backup_retention" {
  description = "Number of days to retain RDS backups"
  type        = number
  default     = 7
}

# -----------------------------------------------------------------------------
# ElastiCache (Redis)
# -----------------------------------------------------------------------------
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.medium"
}

variable "redis_num_cache_nodes" {
  description = "Number of Redis cache nodes"
  type        = number
  default     = 1
}

variable "redis_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.1"
}

# -----------------------------------------------------------------------------
# S3
# -----------------------------------------------------------------------------
# IMPORTANT: S3 bucket names are globally unique across all AWS accounts.
# The defaults below include the environment suffix to reduce collisions, but
# you MUST override these in your .tfvars file with account-specific names
# (e.g., include your AWS account ID or a unique org prefix).
# Recommended pattern: "<org>-<project>-<purpose>-<account-id>-<environment>"
#
# Since Terraform cannot interpolate variables in defaults, use a locals block
# in your root module to build dynamic names:
#   locals {
#     assets_bucket   = "${var.project_prefix}-assets-${data.aws_caller_identity.current.account_id}-${var.environment}"
#     backups_bucket  = "${var.project_prefix}-backups-${data.aws_caller_identity.current.account_id}-${var.environment}"
#     frontend_bucket = "${var.project_prefix}-frontend-${data.aws_caller_identity.current.account_id}-${var.environment}"
#   }

variable "project_prefix" {
  description = "Prefix for resource names including S3 buckets — override to ensure global uniqueness"
  type        = string
  default     = "selfpublisherforge"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.project_prefix))
    error_message = "project_prefix must contain only lowercase letters, numbers, and hyphens, and must not start or end with a hyphen."
  }
}

variable "assets_bucket_name" {
  description = "Name of the S3 bucket for static assets — MUST be globally unique, override in .tfvars"
  type        = string
  default     = "selfpublisherforge-assets-CHANGE-ME"

  validation {
    condition     = var.assets_bucket_name != "selfpublisherforge-assets"
    error_message = "assets_bucket_name 'selfpublisherforge-assets' is not globally unique. Override it in your .tfvars (e.g., 'myorg-selfpublisherforge-assets-123456789012-staging')."
  }
}

variable "backups_bucket_name" {
  description = "Name of the S3 bucket for database backups — MUST be globally unique, override in .tfvars"
  type        = string
  default     = "selfpublisherforge-backups-CHANGE-ME"

  validation {
    condition     = var.backups_bucket_name != "selfpublisherforge-backups"
    error_message = "backups_bucket_name 'selfpublisherforge-backups' is not globally unique. Override it in your .tfvars (e.g., 'myorg-selfpublisherforge-backups-123456789012-staging')."
  }
}

variable "frontend_bucket_name" {
  description = "Name of the S3 bucket for frontend static build output — MUST be globally unique, override in .tfvars"
  type        = string
  default     = "selfpublisherforge-frontend-CHANGE-ME"

  validation {
    condition     = var.frontend_bucket_name != "selfpublisherforge-frontend"
    error_message = "frontend_bucket_name 'selfpublisherforge-frontend' is not globally unique. Override it in your .tfvars (e.g., 'myorg-selfpublisherforge-frontend-123456789012-staging')."
  }
}

# -----------------------------------------------------------------------------
# Monitoring & Logging
# -----------------------------------------------------------------------------
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "flow_log_retention_days" {
  description = "CloudWatch log retention in days for VPC Flow Logs"
  type        = number
  default     = 14
}

variable "alarm_sns_topic_arn" {
  description = "ARN of the SNS topic for CloudWatch alarms"
  type        = string
  default     = ""

  validation {
    condition     = !can(regex("YOUR_AWS_ACCOUNT_ID", var.alarm_sns_topic_arn))
    error_message = "alarm_sns_topic_arn contains 'YOUR_AWS_ACCOUNT_ID'. You must replace this placeholder with your real AWS account ID (e.g., 123456789012)."
  }
}

# -----------------------------------------------------------------------------
# WAF
# -----------------------------------------------------------------------------
variable "waf_rate_limit" {
  description = "Maximum number of requests per 5-minute period per IP before WAF blocks"
  type        = number
  default     = 2000
}

# -----------------------------------------------------------------------------
# Domain / SSL
# -----------------------------------------------------------------------------
variable "domain_name" {
  description = "Primary domain name for the application"
  type        = string
  default     = ""

  # NOTE: Terraform variable validation blocks cannot cross-reference other
  # variables (e.g., var.environment), so this validation ensures the value
  # is not empty whenever it is explicitly provided. The production.tfvars
  # file sets domain_name, so any placeholder or empty value there will be
  # caught at plan time. A truly empty default is fine for staging.
  validation {
    condition     = var.domain_name != "example.com"
    error_message = "domain_name is set to the placeholder 'example.com'. You must replace it with your actual production domain."
  }
}

variable "certificate_arn" {
  description = "ARN of the ACM certificate for HTTPS"
  type        = string
  default     = ""

  validation {
    condition     = !can(regex("REPLACE_ME", var.certificate_arn))
    error_message = "certificate_arn contains 'REPLACE_ME'. You must replace this placeholder with your actual ACM certificate ARN before deploying."
  }

  validation {
    condition     = !can(regex("YOUR_AWS_ACCOUNT_ID", var.certificate_arn))
    error_message = "certificate_arn contains 'YOUR_AWS_ACCOUNT_ID'. You must replace this placeholder with your real AWS account ID (e.g., 123456789012)."
  }
}

# -----------------------------------------------------------------------------
# Secrets (pass via TF_VAR_ environment variables — never commit values)
# -----------------------------------------------------------------------------
variable "jwt_secret_key" {
  description = "JWT signing secret — pass via TF_VAR_jwt_secret_key env variable"
  type        = string
  sensitive   = true
}

variable "app_secret_key" {
  description = "Application secret key (Django SECRET_KEY) — pass via TF_VAR_app_secret_key env variable"
  type        = string
  sensitive   = true
}

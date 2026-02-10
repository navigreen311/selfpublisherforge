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
  description = "CIDR blocks allowed to access the ALB"
  type        = list(string)
  default     = ["0.0.0.0/0"]
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
  default     = "spf_admin"
  sensitive   = true
}

variable "db_password" {
  description = "Master password for the RDS instance"
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
variable "assets_bucket_name" {
  description = "Name of the S3 bucket for static assets"
  type        = string
  default     = "selfpublisherforge-assets"
}

variable "backups_bucket_name" {
  description = "Name of the S3 bucket for database backups"
  type        = string
  default     = "selfpublisherforge-backups"
}

# -----------------------------------------------------------------------------
# Monitoring & Logging
# -----------------------------------------------------------------------------
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "alarm_sns_topic_arn" {
  description = "ARN of the SNS topic for CloudWatch alarms"
  type        = string
  default     = ""
}

# -----------------------------------------------------------------------------
# Domain / SSL
# -----------------------------------------------------------------------------
variable "domain_name" {
  description = "Primary domain name for the application"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ARN of the ACM certificate for HTTPS"
  type        = string
  default     = ""
}

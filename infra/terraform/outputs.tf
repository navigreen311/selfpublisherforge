# =============================================================================
# Terraform Outputs — Key resource identifiers and endpoints
# =============================================================================

# -----------------------------------------------------------------------------
# Networking
# -----------------------------------------------------------------------------
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

# -----------------------------------------------------------------------------
# Load Balancer
# -----------------------------------------------------------------------------
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the ALB (for Route53 alias records)"
  value       = aws_lb.main.zone_id
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

# -----------------------------------------------------------------------------
# ECS
# -----------------------------------------------------------------------------
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "api_service_name" {
  description = "Name of the API ECS service"
  value       = aws_ecs_service.api.name
}

output "frontend_service_name" {
  description = "Name of the Frontend ECS service"
  value       = aws_ecs_service.frontend.name
}

output "worker_service_name" {
  description = "Name of the Worker ECS service"
  value       = aws_ecs_service.worker.name
}

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
output "rds_endpoint" {
  description = "Endpoint of the RDS PostgreSQL instance"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_address" {
  description = "Hostname of the RDS PostgreSQL instance"
  value       = aws_db_instance.postgres.address
}

output "rds_port" {
  description = "Port of the RDS PostgreSQL instance"
  value       = aws_db_instance.postgres.port
}

output "database_url" {
  description = "Full database connection URL (without password)"
  value       = "postgresql+asyncpg://${var.db_username}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${var.db_name}"
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Redis
# -----------------------------------------------------------------------------
output "redis_endpoint" {
  description = "Endpoint of the ElastiCache Redis cluster"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "redis_port" {
  description = "Port of the ElastiCache Redis cluster"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].port
}

output "redis_url" {
  description = "Full Redis connection URL"
  value       = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379/0"
}

# -----------------------------------------------------------------------------
# S3
# -----------------------------------------------------------------------------
output "assets_bucket_name" {
  description = "Name of the S3 assets bucket"
  value       = aws_s3_bucket.assets.id
}

output "assets_bucket_arn" {
  description = "ARN of the S3 assets bucket"
  value       = aws_s3_bucket.assets.arn
}

output "backups_bucket_name" {
  description = "Name of the S3 backups bucket"
  value       = aws_s3_bucket.backups.id
}

# -----------------------------------------------------------------------------
# ECR
# -----------------------------------------------------------------------------
output "ecr_api_repository_url" {
  description = "URL of the API ECR repository"
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_frontend_repository_url" {
  description = "URL of the Frontend ECR repository"
  value       = aws_ecr_repository.frontend.repository_url
}

# -----------------------------------------------------------------------------
# Security Groups
# -----------------------------------------------------------------------------
output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  description = "ID of the ECS security group"
  value       = aws_security_group.ecs.id
}

# -----------------------------------------------------------------------------
# OpenSearch
# -----------------------------------------------------------------------------
output "opensearch_endpoint" {
  description = "Endpoint of the OpenSearch domain"
  value       = aws_opensearch_domain.main.endpoint
}

output "opensearch_dashboard_endpoint" {
  description = "Dashboard endpoint of the OpenSearch domain"
  value       = aws_opensearch_domain.main.dashboard_endpoint
}

output "opensearch_domain_arn" {
  description = "ARN of the OpenSearch domain"
  value       = aws_opensearch_domain.main.arn
}

output "opensearch_domain_id" {
  description = "ID of the OpenSearch domain"
  value       = aws_opensearch_domain.main.domain_id
}

# -----------------------------------------------------------------------------
# Secrets Manager
# -----------------------------------------------------------------------------
output "db_password_secret_arn" {
  description = "ARN of the Secrets Manager secret for the database password"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "jwt_secret_arn" {
  description = "ARN of the Secrets Manager secret for the JWT signing key"
  value       = aws_secretsmanager_secret.jwt_secret.arn
}

output "app_secret_key_arn" {
  description = "ARN of the Secrets Manager secret for the application secret key"
  value       = aws_secretsmanager_secret.app_secret_key.arn
}

output "database_url_secret_arn" {
  description = "ARN of the Secrets Manager secret for the full database URL"
  value       = aws_secretsmanager_secret.database_url.arn
}

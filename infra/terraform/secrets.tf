# =============================================================================
# Secrets Manager — Centralized secret storage for all sensitive values
# =============================================================================

# -----------------------------------------------------------------------------
# Database Password
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret" "db_password" {
  name        = "${var.project_name}-${var.environment}-db-password"
  description = "RDS PostgreSQL master password for ${var.environment}"

  tags = {
    Name = "${var.project_name}-${var.environment}-db-password"
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password
}

# -----------------------------------------------------------------------------
# JWT Secret Key
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret" "jwt_secret" {
  name        = "${var.project_name}-${var.environment}-jwt-secret"
  description = "JWT signing secret for ${var.environment}"

  tags = {
    Name = "${var.project_name}-${var.environment}-jwt-secret"
  }
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = var.jwt_secret_key
}

# -----------------------------------------------------------------------------
# Django / App Secret Key
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret" "app_secret_key" {
  name        = "${var.project_name}-${var.environment}-app-secret-key"
  description = "Application secret key (Django SECRET_KEY) for ${var.environment}"

  tags = {
    Name = "${var.project_name}-${var.environment}-app-secret-key"
  }
}

resource "aws_secretsmanager_secret_version" "app_secret_key" {
  secret_id     = aws_secretsmanager_secret.app_secret_key.id
  secret_string = var.app_secret_key
}

# -----------------------------------------------------------------------------
# Database URL (composed secret)
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret" "database_url" {
  name        = "${var.project_name}-${var.environment}-database-url"
  description = "Full database connection URL for ${var.environment}"

  tags = {
    Name = "${var.project_name}-${var.environment}-database-url"
  }
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${var.db_name}"
}

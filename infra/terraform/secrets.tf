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

# =============================================================================
# Secrets Rotation — Automatic 30-day rotation for all secrets
# =============================================================================

# -----------------------------------------------------------------------------
# Security Group for Rotation Lambda (VPC access to RDS and Secrets Manager)
# -----------------------------------------------------------------------------
resource "aws_security_group" "rotation_lambda" {
  name_prefix = "${var.project_name}-${var.environment}-rotation-lambda-"
  description = "Security group for Secrets Manager rotation Lambda"
  vpc_id      = aws_vpc.main.id

  egress {
    description = "All outbound (Secrets Manager API and RDS access)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-rotation-lambda-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Allow rotation Lambda to connect to RDS
resource "aws_security_group_rule" "rds_from_rotation_lambda" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.rotation_lambda.id
  security_group_id        = aws_security_group.rds.id
  description              = "PostgreSQL from rotation Lambda"
}

# -----------------------------------------------------------------------------
# Secrets Manager VPC Endpoint (rotation Lambda needs API access from VPC)
# -----------------------------------------------------------------------------
# Network path: Lambda (private subnet) → VPC Endpoint ENI → Secrets Manager API
# With private_dns_enabled = true, the standard secretsmanager.<region>.amazonaws.com
# hostname resolves to the VPC endpoint's private IP within the VPC. We also pass
# the VPC endpoint DNS name explicitly to the Lambda via SECRETS_MANAGER_ENDPOINT
# to guarantee traffic never leaves the VPC (no NAT gateway required).
resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.rotation_lambda.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-secretsmanager-endpoint"
  }
}

# -----------------------------------------------------------------------------
# AWS-Managed PostgreSQL Rotation Lambda (via Serverless Application Repository)
# -----------------------------------------------------------------------------
resource "aws_serverlessapplicationrepository_cloudformation_stack" "db_password_rotation" {
  name           = "${var.project_name}-${var.environment}-db-rotation"
  application_id = "arn:aws:serverlessrepo:us-east-1:297356227824:applications/SecretsManagerRDSPostgreSQLRotationSingleUser"

  capabilities = ["CAPABILITY_IAM", "CAPABILITY_RESOURCE_POLICY"]

  parameters = {
    functionName = "${var.project_name}-${var.environment}-db-password-rotation"
    # Route Secrets Manager API calls through the VPC endpoint (private link)
    # instead of the public internet endpoint. This avoids NAT gateway dependency.
    endpoint            = "https://${aws_vpc_endpoint.secretsmanager.dns_entry[0].dns_name}"
    vpcSubnetIds        = join(",", aws_subnet.private[*].id)
    vpcSecurityGroupIds = aws_security_group.rotation_lambda.id
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-db-rotation-stack"
  }
}

# -----------------------------------------------------------------------------
# DB Password Rotation (30-day schedule)
# Rotation cadence: every 30 days. Adjust automatically_after_days to change.
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret_rotation" "db_password" {
  secret_id           = aws_secretsmanager_secret.db_password.id
  rotation_lambda_arn = aws_serverlessapplicationrepository_cloudformation_stack.db_password_rotation.outputs["RotationLambdaARN"]

  rotation_rules {
    # 30-day rotation complies with security best practices.
    automatically_after_days = 30
  }

  depends_on = [aws_vpc_endpoint.secretsmanager]
}

# -----------------------------------------------------------------------------
# Generic Rotation Lambda for Application Secrets (JWT, App Key)
# -----------------------------------------------------------------------------
resource "aws_iam_role" "secret_rotation" {
  name = "${var.project_name}-${var.environment}-secret-rotation-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-secret-rotation-role"
  }
}

resource "aws_iam_role_policy" "secret_rotation" {
  name = "${var.project_name}-${var.environment}-secret-rotation-policy"
  role = aws_iam_role.secret_rotation.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret",
          "secretsmanager:PutSecretValue",
          "secretsmanager:UpdateSecretVersionStage"
        ]
        Resource = [
          aws_secretsmanager_secret.jwt_secret.arn,
          aws_secretsmanager_secret.app_secret_key.arn,
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetRandomPassword"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DeleteNetworkInterface",
          "ec2:DescribeNetworkInterfaces"
        ]
        Resource = "*"
      }
    ]
  })
}

data "archive_file" "secret_rotation" {
  type        = "zip"
  output_path = "${path.module}/lambda/generic_secret_rotation.zip"

  source {
    content  = <<-PYTHON
import boto3
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def _get_client():
    """Create a Secrets Manager client using the VPC endpoint URL."""
    endpoint = os.environ.get('SECRETS_MANAGER_ENDPOINT')
    logger.info("Connecting to Secrets Manager via endpoint: %s", endpoint)
    return boto3.client('secretsmanager', endpoint_url=endpoint)

def _health_check(client):
    """Verify connectivity to Secrets Manager through the VPC endpoint.

    Calls GetRandomPassword as a lightweight connectivity test before
    performing any rotation steps. Raises an exception if the endpoint
    is unreachable, which causes the rotation to fail fast with a clear
    error rather than timing out silently.
    """
    try:
        client.get_random_password(PasswordLength=8)
        logger.info("Health check passed: Secrets Manager endpoint is reachable")
    except Exception as e:
        logger.error("Health check FAILED: Cannot reach Secrets Manager endpoint. "
                     "Verify VPC endpoint configuration and security group rules. Error: %s", e)
        raise RuntimeError(
            "Secrets Manager endpoint unreachable. Ensure the VPC endpoint "
            "(com.amazonaws.<region>.secretsmanager) is active and the Lambda "
            "security group allows HTTPS (443) egress to the endpoint."
        ) from e

def lambda_handler(event, context):
    """Rotates a generic secret by generating a new random password.

    Network path: Lambda (private subnet) -> VPC Endpoint ENI -> Secrets Manager API.
    No NAT gateway or internet access is required.
    """
    secret_arn = event['SecretId']
    token      = event['ClientRequestToken']
    step       = event['Step']

    logger.info("Rotation step '%s' for secret %s (token: %s)", step, secret_arn, token)

    client = _get_client()

    # Validate Secrets Manager connectivity before any rotation step
    _health_check(client)

    if step == "createSecret":
        # Generate a new secret value
        passwd = client.get_random_password(
            PasswordLength=64,
            ExcludeCharacters='"@/\\',
            RequireEachIncludedType=True
        )
        client.put_secret_value(
            SecretId=secret_arn,
            ClientRequestToken=token,
            SecretString=passwd['RandomPassword'],
            VersionStages=['AWSPENDING']
        )
        logger.info("createSecret: new pending version stored")

    elif step == "setSecret":
        # No external system to update for generic secrets
        pass

    elif step == "testSecret":
        # Verify the pending secret can be retrieved
        client.get_secret_value(
            SecretId=secret_arn,
            VersionId=token,
            VersionStage='AWSPENDING'
        )
        logger.info("testSecret: pending version retrieved successfully")

    elif step == "finishSecret":
        # Promote AWSPENDING to AWSCURRENT
        metadata = client.describe_secret(SecretId=secret_arn)
        current_version = None
        for version_id, stages in metadata['VersionIdsToStages'].items():
            if 'AWSCURRENT' in stages and version_id != token:
                current_version = version_id
                break

        client.update_secret_version_stage(
            SecretId=secret_arn,
            VersionStage='AWSCURRENT',
            MoveToVersionId=token,
            RemoveFromVersionId=current_version
        )
        logger.info("finishSecret: version %s promoted to AWSCURRENT", token)

    return {"statusCode": 200}
    PYTHON
    filename = "index.py"
  }
}

# Network path: Lambda (private subnet) -> VPC Endpoint ENI -> Secrets Manager API
# The Lambda runs inside the VPC with no internet access. It reaches
# Secrets Manager exclusively through the VPC Interface Endpoint, so no
# NAT gateway is needed. The SECRETS_MANAGER_ENDPOINT env var points to the
# VPC endpoint's DNS name to guarantee all API traffic stays within the VPC.
resource "aws_lambda_function" "secret_rotation" {
  function_name = "${var.project_name}-${var.environment}-generic-secret-rotation"
  description   = "Rotates application secrets (JWT, App Key) by generating new random values"
  role          = aws_iam_role.secret_rotation.arn
  runtime       = "python3.12"
  handler       = "index.lambda_handler"
  timeout       = 60

  filename         = data.archive_file.secret_rotation.output_path
  source_code_hash = data.archive_file.secret_rotation.output_base64sha256

  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.rotation_lambda.id]
  }

  environment {
    variables = {
      # Use VPC endpoint DNS instead of the public Secrets Manager endpoint.
      # This ensures the Lambda communicates via private link, avoiding the
      # need for a NAT gateway or internet gateway.
      SECRETS_MANAGER_ENDPOINT = "https://${aws_vpc_endpoint.secretsmanager.dns_entry[0].dns_name}"
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-generic-secret-rotation"
  }

  depends_on = [aws_vpc_endpoint.secretsmanager]
}

resource "aws_lambda_permission" "jwt_secret_rotation" {
  statement_id  = "AllowSecretsManagerJWT"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.secret_rotation.function_name
  principal     = "secretsmanager.amazonaws.com"
  source_arn    = aws_secretsmanager_secret.jwt_secret.arn
}

resource "aws_lambda_permission" "app_secret_rotation" {
  statement_id  = "AllowSecretsManagerAppKey"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.secret_rotation.function_name
  principal     = "secretsmanager.amazonaws.com"
  source_arn    = aws_secretsmanager_secret.app_secret_key.arn
}

# -----------------------------------------------------------------------------
# JWT Secret Rotation (30-day schedule)
# Rotation cadence: every 30 days. Adjust automatically_after_days to change.
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret_rotation" "jwt_secret" {
  secret_id           = aws_secretsmanager_secret.jwt_secret.id
  rotation_lambda_arn = aws_lambda_function.secret_rotation.arn

  rotation_rules {
    # 30-day rotation complies with security best practices.
    automatically_after_days = 30
  }

  depends_on = [
    aws_lambda_permission.jwt_secret_rotation,
    aws_vpc_endpoint.secretsmanager,
  ]
}

# -----------------------------------------------------------------------------
# App Secret Key Rotation (30-day schedule)
# Rotation cadence: every 30 days. Adjust automatically_after_days to change.
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret_rotation" "app_secret_key" {
  secret_id           = aws_secretsmanager_secret.app_secret_key.id
  rotation_lambda_arn = aws_lambda_function.secret_rotation.arn

  rotation_rules {
    # 30-day rotation complies with security best practices.
    automatically_after_days = 30
  }

  depends_on = [
    aws_lambda_permission.app_secret_rotation,
    aws_vpc_endpoint.secretsmanager,
  ]
}

# NOTE: database_url is a composed secret derived from db_password. When
# db_password rotates, the rotation Lambda should also update database_url.
# This is typically handled by customizing the PostgreSQL rotation Lambda's
# finishSecret step to reconstruct and store the new connection URL.

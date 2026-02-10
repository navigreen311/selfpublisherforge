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
    functionName    = "${var.project_name}-${var.environment}-db-password-rotation"
    endpoint        = "https://secretsmanager.${var.aws_region}.amazonaws.com"
    vpcSubnetIds    = join(",", aws_subnet.private[*].id)
    vpcSecurityGroupIds = aws_security_group.rotation_lambda.id
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-db-rotation-stack"
  }
}

# -----------------------------------------------------------------------------
# DB Password Rotation (30-day schedule)
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret_rotation" "db_password" {
  secret_id           = aws_secretsmanager_secret.db_password.id
  rotation_lambda_arn = aws_serverlessapplicationrepository_cloudformation_stack.db_password_rotation.outputs["RotationLambdaARN"]

  rotation_rules {
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
import os

def lambda_handler(event, context):
    """Rotates a generic secret by generating a new random password."""
    secret_arn = event['SecretId']
    token      = event['ClientRequestToken']
    step       = event['Step']

    client = boto3.client('secretsmanager',
        endpoint_url=os.environ.get('SECRETS_MANAGER_ENDPOINT'))

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

    return {"statusCode": 200}
    PYTHON
    filename = "index.py"
  }
}

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
      SECRETS_MANAGER_ENDPOINT = "https://secretsmanager.${var.aws_region}.amazonaws.com"
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
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret_rotation" "jwt_secret" {
  secret_id           = aws_secretsmanager_secret.jwt_secret.id
  rotation_lambda_arn = aws_lambda_function.secret_rotation.arn

  rotation_rules {
    automatically_after_days = 30
  }

  depends_on = [
    aws_lambda_permission.jwt_secret_rotation,
    aws_vpc_endpoint.secretsmanager,
  ]
}

# -----------------------------------------------------------------------------
# App Secret Key Rotation (30-day schedule)
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret_rotation" "app_secret_key" {
  secret_id           = aws_secretsmanager_secret.app_secret_key.id
  rotation_lambda_arn = aws_lambda_function.secret_rotation.arn

  rotation_rules {
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

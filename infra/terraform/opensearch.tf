# =============================================================================
# OpenSearch — Full-text search for knowledge vault and market intelligence
# =============================================================================

# -----------------------------------------------------------------------------
# Service-Linked Role (required for VPC access)
# -----------------------------------------------------------------------------
resource "aws_iam_service_linked_role" "opensearch" {
  aws_service_name = "opensearchservice.amazonaws.com"
}

# -----------------------------------------------------------------------------
# Security Group
# -----------------------------------------------------------------------------
resource "aws_security_group" "opensearch" {
  name_prefix = "${var.project_name}-${var.environment}-opensearch-"
  description = "Security group for OpenSearch domain"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "HTTPS from ECS"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-opensearch-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# -----------------------------------------------------------------------------
# CloudWatch Log Groups for OpenSearch
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "opensearch_index_slow" {
  name              = "/opensearch/${var.project_name}-${var.environment}/index-slow-logs"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "opensearch_search_slow" {
  name              = "/opensearch/${var.project_name}-${var.environment}/search-slow-logs"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "opensearch_es_app" {
  name              = "/opensearch/${var.project_name}-${var.environment}/es-application-logs"
  retention_in_days = var.log_retention_days
}

# -----------------------------------------------------------------------------
# CloudWatch Log Resource Policy (allows OpenSearch to write logs)
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_log_resource_policy" "opensearch" {
  policy_name = "${var.project_name}-${var.environment}-opensearch-log-policy"

  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "es.amazonaws.com"
        }
        Action = [
          "logs:PutLogEvents",
          "logs:PutLogEventsBatch",
          "logs:CreateLogStream",
        ]
        Resource = [
          "${aws_cloudwatch_log_group.opensearch_index_slow.arn}:*",
          "${aws_cloudwatch_log_group.opensearch_search_slow.arn}:*",
          "${aws_cloudwatch_log_group.opensearch_es_app.arn}:*",
        ]
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# OpenSearch Domain
# -----------------------------------------------------------------------------
resource "aws_opensearch_domain" "main" {
  domain_name    = "${var.project_name}-${var.environment}"
  engine_version = "OpenSearch_2.11"

  cluster_config {
    instance_type          = var.environment == "production" ? "t3.medium.search" : "t3.small.search"
    instance_count         = var.environment == "production" ? 2 : 1
    zone_awareness_enabled = var.environment == "production" ? true : false

    dynamic "zone_awareness_config" {
      for_each = var.environment == "production" ? [1] : []
      content {
        availability_zone_count = 2
      }
    }
  }

  ebs_options {
    ebs_enabled = true
    volume_size = var.environment == "production" ? 50 : 20
    volume_type = "gp3"
  }

  encrypt_at_rest {
    enabled = true
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  vpc_options {
    subnet_ids         = var.environment == "production" ? [aws_subnet.private[0].id, aws_subnet.private[1].id] : [aws_subnet.private[0].id]
    security_group_ids = [aws_security_group.opensearch.id]
  }

  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { AWS = "*" }
        Action    = "es:*"
        Resource  = "arn:aws:es:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:domain/${var.project_name}-${var.environment}/*"
      }
    ]
  })

  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch_index_slow.arn
    log_type                 = "INDEX_SLOW_LOGS"
  }

  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch_search_slow.arn
    log_type                 = "SEARCH_SLOW_LOGS"
  }

  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch_es_app.arn
    log_type                 = "ES_APPLICATION_LOGS"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-opensearch"
  }

  depends_on = [
    aws_iam_service_linked_role.opensearch,
    aws_cloudwatch_log_resource_policy.opensearch,
  ]
}

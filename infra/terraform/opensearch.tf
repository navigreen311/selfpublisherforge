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

  # Access policy: restrict to ECS task role only (least-privilege principle)
  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { AWS = aws_iam_role.ecs_task.arn }
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

# -----------------------------------------------------------------------------
# ISM (Index State Management) Policy
# -----------------------------------------------------------------------------
# OpenSearch ISM manages the index lifecycle automatically. This policy defines
# three phases for selfpublisherforge-* indices:
#
#   1. HOT (days 0-30)  — Active indexing and querying. Standard replicas.
#   2. WARM (days 30-90) — Read-optimized. Replicas reduced to 0, segments
#                          force-merged to 1 for smaller disk footprint.
#                          If UltraWarm is enabled on the cluster, indices
#                          migrate to warm storage in this phase.
#   3. DELETE (day 90+)  — Index is permanently deleted to reclaim storage.
#
# The policy is applied via the OpenSearch _plugins/_ism REST API using a
# null_resource provisioner, since the AWS Terraform provider does not have
# a native ISM policy resource.
# -----------------------------------------------------------------------------

locals {
  ism_policy_name = "selfpublisherforge_index_retention"

  ism_policy = jsonencode({
    policy = {
      description   = "Index lifecycle policy for SelfPublisherForge — hot(30d) -> warm(60d) -> delete"
      default_state = "hot"

      states = [
        {
          name    = "hot"
          actions = []
          transitions = [
            {
              state_name = "warm"
              conditions = {
                min_index_age = "30d"
              }
            }
          ]
        },
        {
          name = "warm"
          actions = [
            {
              replica_count = {
                number_of_replicas = 0
              }
            },
            {
              force_merge = {
                max_num_segments = 1
              }
            }
          ]
          transitions = [
            {
              state_name = "delete"
              conditions = {
                min_index_age = "90d"
              }
            }
          ]
        },
        {
          name = "delete"
          actions = [
            {
              delete = {}
            }
          ]
          transitions = []
        }
      ]

      ism_template = [
        {
          index_patterns = ["selfpublisherforge-*"]
          priority       = 100
        }
      ]
    }
  })
}

# Write the ISM policy JSON to a local file so it can be inspected, versioned,
# and applied via the OpenSearch REST API.
resource "local_file" "ism_policy" {
  content  = local.ism_policy
  filename = "${path.module}/generated/ism_policy.json"
}

# Apply the ISM policy to the OpenSearch domain via the _plugins/_ism API.
# This runs after the domain is fully provisioned. The provisioner uses curl
# to PUT the policy document. On subsequent applies, it will update the
# existing policy (OpenSearch upserts on PUT with seq_no/primary_term, but
# for initial creation a simple PUT suffices).
#
# NOTE: This provisioner runs from a machine that has network access to the
# OpenSearch VPC endpoint (e.g., a bastion host, VPN, or CI runner inside
# the VPC). If running from outside the VPC, you will need to configure
# an SSH tunnel or use AWS Session Manager port forwarding first.
resource "null_resource" "opensearch_ism_policy" {
  triggers = {
    # Re-apply whenever the policy content changes
    policy_hash = sha256(local.ism_policy)
    # Re-apply if the domain is recreated
    domain_endpoint = aws_opensearch_domain.main.endpoint
  }

  provisioner "local-exec" {
    command = <<-EOT
      curl -s -o /dev/null -w "%%{http_code}" \
        -X PUT \
        -H "Content-Type: application/json" \
        -d '${replace(local.ism_policy, "'", "'\\''")}' \
        "https://${aws_opensearch_domain.main.endpoint}/_plugins/_ism/policies/${local.ism_policy_name}" \
        --aws-sigv4 "aws:amz:${data.aws_region.current.name}:es" \
        --user "${data.aws_caller_identity.current.account_id}:" \
        | grep -qE "^(200|201)"
    EOT

    interpreter = ["bash", "-c"]
  }

  depends_on = [
    aws_opensearch_domain.main,
    local_file.ism_policy,
  ]
}

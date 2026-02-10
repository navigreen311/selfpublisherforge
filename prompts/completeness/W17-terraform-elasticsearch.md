# W17: Terraform — Add Elasticsearch/OpenSearch Module

## Files to create
- `infra/terraform/opensearch.tf` — NEW

## Files to modify
- `infra/terraform/outputs.tf` — Add OpenSearch endpoint output

## Context
The backend uses full-text search (knowledge vault, market intelligence) but has no Elasticsearch/OpenSearch infrastructure defined in Terraform.

## Task

### 1. Create opensearch.tf

```hcl
resource "aws_opensearch_domain" "main" {
  domain_name    = "${var.project_name}-${var.environment}"
  engine_version = "OpenSearch_2.11"

  cluster_config {
    instance_type          = var.environment == "production" ? "t3.medium.search" : "t3.small.search"
    instance_count         = var.environment == "production" ? 2 : 1
    zone_awareness_enabled = var.environment == "production" ? true : false
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
    subnet_ids         = var.environment == "production" ? [var.private_subnet_ids[0], var.private_subnet_ids[1]] : [var.private_subnet_ids[0]]
    security_group_ids = [aws_security_group.opensearch.id]
  }

  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = "*" }
      Action    = "es:*"
      Resource  = "arn:aws:es:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:domain/${var.project_name}-${var.environment}/*"
    }]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-opensearch"
    Environment = var.environment
  }
}

resource "aws_security_group" "opensearch" {
  name_prefix = "${var.project_name}-opensearch-"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }

  tags = {
    Name = "${var.project_name}-opensearch-sg"
  }
}
```

### 2. Add variables (if needed)

Check if `private_subnet_ids`, `vpc_id`, `app_security_group_id` variables exist. If not, add them to variables.tf.

### 3. Add outputs

```hcl
output "opensearch_endpoint" {
  value = aws_opensearch_domain.main.endpoint
}

output "opensearch_dashboard_endpoint" {
  value = aws_opensearch_domain.main.dashboard_endpoint
}
```

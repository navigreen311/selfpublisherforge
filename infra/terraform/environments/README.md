# Terraform Environment Configurations

This directory contains per-environment variable override files (`.tfvars`) used
to deploy the **SelfPublisherForge** infrastructure into AWS.

| File | Purpose |
|------|---------|
| `production.tfvars` | Production environment overrides -- larger instances, Multi-AZ RDS, longer log retention |
| `staging.tfvars` | Staging environment overrides -- smaller instances, single-AZ RDS, shorter retention |

---

## First-Time Setup Guide

If you are deploying SelfPublisherForge infrastructure for the first time, follow
these steps **in order** before running `terraform apply`.

### 1. Install Prerequisites

| Tool | Minimum Version | Check Command |
|------|-----------------|---------------|
| AWS CLI | 2.x | `aws --version` |
| Terraform | >= 1.6.0 | `terraform version` |
| Git | any | `git --version` |

### 2. Configure AWS Credentials

```bash
aws configure
# Provide: Access Key ID, Secret Access Key, default region (us-east-1), output format (json)

# Verify access:
aws sts get-caller-identity
```

### 3. Create the Terraform State Backend

Terraform stores its state in S3 with DynamoDB locking. These resources must
exist **before** `terraform init`.

```bash
# Create the S3 state bucket
aws s3api create-bucket \
  --bucket selfpublisherforge-terraform-state \
  --region us-east-1

# Enable versioning on the state bucket (protects against accidental deletes)
aws s3api put-bucket-versioning \
  --bucket selfpublisherforge-terraform-state \
  --versioning-configuration Status=Enabled

# Enable server-side encryption by default
aws s3api put-bucket-encryption \
  --bucket selfpublisherforge-terraform-state \
  --server-side-encryption-configuration \
    '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# Block public access to the state bucket
aws s3api put-public-access-block \
  --bucket selfpublisherforge-terraform-state \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Create the DynamoDB lock table
aws dynamodb create-table \
  --table-name selfpublisherforge-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### 4. Request an ACM Certificate (Production, or Staging with Custom Domain)

See [Obtaining an ACM Certificate](#obtaining-an-acm-certificate) below for
step-by-step instructions. This must be done and fully validated **before**
deploying, because Terraform references the certificate ARN.

### 5. Create an SNS Topic (Production)

See [Creating an SNS Topic](#creating-an-sns-topic) below for step-by-step
instructions. Confirm the email subscription before deploying.

### 6. Set Up DNS (if using a custom domain)

See [Setting Up DNS (Route 53)](#setting-up-dns-route-53) below. You will need
the Terraform outputs after the first apply to complete DNS record creation.

---

## Complete Variable Reference

The table below lists **every** variable defined in `variables.tf`, its type,
default value, and whether it must be explicitly set in each environment.

### Infrastructure Variables (set in `.tfvars` files)

| Variable | Type | Default | Staging | Production | Description |
|----------|------|---------|---------|------------|-------------|
| `environment` | string | `"staging"` | Set to `"staging"` | Set to `"production"` | Deployment environment name |
| `aws_region` | string | `"us-east-1"` | Set | Set | AWS region for all resources |
| `project_name` | string | `"selfpublisherforge"` | Uses default | Uses default | Resource name prefix |
| `vpc_cidr` | string | `"10.0.0.0/16"` | Uses default | Uses default | CIDR block for the VPC |
| `availability_zones_count` | number | `2` | Uses default | Uses default | Number of AZs to use |
| `allowed_cidr_blocks` | list(string) | `[]` | **REQUIRED** | **REQUIRED** | CIDR blocks allowed to access ALB |
| `api_cpu` | number | `512` | `256` | `512` | CPU units for API ECS task |
| `api_memory` | number | `1024` | `512` | `1024` | Memory (MiB) for API ECS task |
| `api_desired_count` | number | `2` | `1` | `2` | Desired API task instances |
| `api_min_count` | number | `2` | `1` | `2` | Auto-scaling floor for API |
| `api_max_count` | number | `10` | `3` | `10` | Auto-scaling ceiling for API |
| `frontend_cpu` | number | `256` | `256` | `256` | CPU units for Frontend ECS task |
| `frontend_memory` | number | `512` | `512` | `512` | Memory (MiB) for Frontend ECS task |
| `frontend_desired_count` | number | `2` | `1` | `2` | Desired Frontend task instances |
| `worker_cpu` | number | `512` | `256` | `512` | CPU units for Celery worker task |
| `worker_memory` | number | `1024` | `512` | `1024` | Memory (MiB) for Celery worker task |
| `worker_desired_count` | number | `2` | `1` | `2` | Desired Celery worker instances |
| `beat_cpu` | number | `256` | `256` | `256` | CPU units for Celery beat task |
| `beat_memory` | number | `512` | `256` | `512` | Memory (MiB) for Celery beat task |
| `db_instance_class` | string | `"db.t3.medium"` | `"db.t3.small"` | `"db.t3.medium"` | RDS instance class |
| `db_allocated_storage` | number | `50` | `20` | `50` | Initial RDS storage (GB) |
| `db_max_allocated_storage` | number | `200` | `50` | `200` | Max RDS storage for auto-scaling (GB) |
| `db_name` | string | `"selfpublisherforge"` | Uses default | Uses default | PostgreSQL database name |
| `db_multi_az` | bool | `false` | `false` | `true` | Multi-AZ for RDS high availability |
| `db_backup_retention` | number | `7` | `3` | `7` | Days to retain RDS backups |
| `redis_node_type` | string | `"cache.t3.medium"` | `"cache.t3.small"` | `"cache.t3.medium"` | ElastiCache node type |
| `redis_num_cache_nodes` | number | `1` | `1` | `1` | Number of Redis nodes |
| `redis_engine_version` | string | `"7.1"` | Uses default | Uses default | Redis engine version |
| `assets_bucket_name` | string | `"selfpublisherforge-assets"` | Override recommended | Uses default | S3 bucket for assets |
| `backups_bucket_name` | string | `"selfpublisherforge-backups"` | Override recommended | Uses default | S3 bucket for DB backups |
| `frontend_bucket_name` | string | `"selfpublisherforge-frontend"` | Override recommended | Uses default | S3 bucket for frontend builds |
| `log_retention_days` | number | `30` | `14` | `30` | CloudWatch log retention (days) |
| `flow_log_retention_days` | number | `14` | Uses default | Uses default | VPC Flow Log retention (days) |
| `waf_rate_limit` | number | `2000` | Uses default | Uses default | WAF rate limit (requests per 5 min per IP) |
| `domain_name` | string | `""` | Optional | **REQUIRED** | Primary domain name |
| `certificate_arn` | string | `""` | Optional | **REQUIRED** | ACM certificate ARN for HTTPS |
| `alarm_sns_topic_arn` | string | `""` | Optional | **REQUIRED** | SNS topic ARN for CloudWatch alarms |

### Secret Variables (set as environment variables -- NEVER in `.tfvars` files)

| Environment Variable | Type | Required | Description | How to Generate |
|----------------------|------|----------|-------------|-----------------|
| `TF_VAR_db_username` | string | Yes | RDS PostgreSQL master username | Choose a username, e.g. `spf_admin` |
| `TF_VAR_db_password` | string | Yes | RDS PostgreSQL master password (>= 16 chars) | `openssl rand -base64 24` |
| `TF_VAR_jwt_secret_key` | string | Yes | JWT signing secret for the API | `openssl rand -hex 32` |
| `TF_VAR_app_secret_key` | string | Yes | Django `SECRET_KEY` | `openssl rand -hex 50` |

> **Important:** Use **different** secret values for staging and production to
> maintain security isolation between environments.

---

## Deployment Checklist

### One-Time AWS Account Setup

1. [ ] AWS CLI installed and configured (`aws configure`)
2. [ ] Terraform >= 1.6.0 installed (`terraform version`)
3. [ ] S3 state bucket created: `selfpublisherforge-terraform-state`
4. [ ] DynamoDB lock table created: `selfpublisherforge-terraform-locks`
5. [ ] ECR repositories will be created by Terraform (no manual action needed)

### Per-Environment Pre-Deploy Steps

1. [ ] All `TODO` placeholders in the `.tfvars` file have been replaced with real values
2. [ ] `allowed_cidr_blocks` is set to a non-empty list of CIDR ranges
3. [ ] `TF_VAR_db_username` exported in shell
4. [ ] `TF_VAR_db_password` exported in shell (>= 16 characters)
5. [ ] `TF_VAR_jwt_secret_key` exported in shell
6. [ ] `TF_VAR_app_secret_key` exported in shell
7. [ ] `terraform init` has been run from the `infra/terraform/` directory
8. [ ] `terraform plan -var-file=environments/<env>.tfvars` reviewed with no unexpected changes

### Production-Specific Checks

1. [ ] `domain_name` is set to the real production domain (e.g., `selfpublisherforge.com`)
2. [ ] `certificate_arn` points to a **validated** ACM certificate in `us-east-1`
3. [ ] `alarm_sns_topic_arn` points to an active SNS topic with **confirmed** subscribers
4. [ ] `db_multi_az` is `true`
5. [ ] S3 bucket names do not collide with staging buckets
6. [ ] DNS records are ready to be created post-deploy (see [Setting Up DNS](#setting-up-dns-route-53))
7. [ ] Review the `terraform plan` output carefully -- production changes are irreversible for some resources (e.g., RDS)

### Staging-Specific Checks

1. [ ] S3 bucket names are overridden to avoid collision with production (e.g., `selfpublisherforge-assets-staging`)
2. [ ] `allowed_cidr_blocks` is set (open or restricted to your IP/VPN)
3. [ ] `domain_name` and `certificate_arn` are either both set or both empty

---

## Deployment Commands

### Initialize Terraform (first time or after backend changes)

```bash
cd infra/terraform

terraform init
```

### Staging

```bash
# Export secrets
export TF_VAR_db_username="spf_staging_admin"
export TF_VAR_db_password="$(openssl rand -base64 24)"
export TF_VAR_jwt_secret_key="$(openssl rand -hex 32)"
export TF_VAR_app_secret_key="$(openssl rand -hex 50)"

# Preview changes
terraform plan -var-file=environments/staging.tfvars

# Apply (with manual approval)
terraform apply -var-file=environments/staging.tfvars

# Destroy staging when no longer needed
terraform destroy -var-file=environments/staging.tfvars
```

### Production

```bash
# Export secrets (use your real, securely stored values -- not random ones)
export TF_VAR_db_username="spf_admin"
export TF_VAR_db_password="<your-secure-password>"
export TF_VAR_jwt_secret_key="<your-jwt-secret>"
export TF_VAR_app_secret_key="<your-django-secret>"

# Preview changes -- ALWAYS review the plan before applying to production
terraform plan -var-file=environments/production.tfvars

# Apply (with manual approval)
terraform apply -var-file=environments/production.tfvars
```

> **Tip:** For CI/CD pipelines, store the four secret values in your pipeline's
> secret manager (GitHub Actions secrets, AWS Secrets Manager, etc.) and inject
> them as `TF_VAR_*` environment variables at runtime.

---

## Obtaining an ACM Certificate

CloudFront requires the certificate to be in **us-east-1** regardless of your
application region.

```bash
# Step 1 -- Request a certificate (with wildcard for subdomains)
aws acm request-certificate \
  --domain-name selfpublisherforge.com \
  --subject-alternative-names "*.selfpublisherforge.com" \
  --validation-method DNS \
  --region us-east-1

# The output includes a CertificateArn. Save it.

# Step 2 -- Retrieve the DNS validation records
aws acm describe-certificate \
  --certificate-arn <CertificateArn> \
  --region us-east-1 \
  --query 'Certificate.DomainValidationOptions[].ResourceRecord'

# Step 3 -- Create the CNAME record(s) shown above in your DNS provider
#          (Route 53, Cloudflare, Namecheap, etc.)

# Step 4 -- Wait for the certificate to validate (5-30 minutes)
aws acm wait certificate-validated \
  --certificate-arn <CertificateArn> \
  --region us-east-1

# Step 5 -- Copy the CertificateArn into the certificate_arn field in your tfvars file
```

If you manage DNS in **Route 53**, you can automate validation:

```bash
HOSTED_ZONE_ID=Z0123456789ABCDEFGHIJ  # your Route 53 hosted zone ID

aws acm request-certificate \
  --domain-name selfpublisherforge.com \
  --subject-alternative-names "*.selfpublisherforge.com" \
  --validation-method DNS \
  --region us-east-1

# Then use the AWS Console or the route53 CLI to create the validation records.
```

---

## Creating an SNS Topic

The SNS topic receives CloudWatch Alarm notifications (CPU spikes, unhealthy
targets, high error rates, etc.).

```bash
# Step 1 -- Create the topic
aws sns create-topic \
  --name selfpublisherforge-production-alarms \
  --region us-east-1

# The output includes a TopicArn. Save it.

# Step 2 -- Subscribe your email
aws sns subscribe \
  --topic-arn <TopicArn> \
  --protocol email \
  --notification-endpoint ops-team@example.com \
  --region us-east-1

# Step 3 -- Check your inbox and click the confirmation link from AWS.

# Step 4 -- (Optional) Add a PagerDuty / Slack / OpsGenie webhook
aws sns subscribe \
  --topic-arn <TopicArn> \
  --protocol https \
  --notification-endpoint https://events.pagerduty.com/integration/<key>/enqueue

# Step 5 -- Paste the TopicArn into the alarm_sns_topic_arn field in production.tfvars
```

---

## Setting Up DNS (Route 53)

If your domain registrar is not Route 53, point your registrar's nameservers to
the Route 53 hosted zone. After Terraform creates the ALB and CloudFront
distribution, create DNS records:

| Record | Type | Target |
|--------|------|--------|
| `selfpublisherforge.com` | A (Alias) | CloudFront distribution domain |
| `www.selfpublisherforge.com` | CNAME | CloudFront distribution domain |
| `api.selfpublisherforge.com` | A (Alias) | ALB DNS name |

Terraform outputs will provide the exact values after `terraform apply`.

---

## Troubleshooting

### `terraform init` fails with "AccessDenied" for S3 backend

The S3 state bucket or DynamoDB lock table does not exist, or your IAM
user/role lacks permissions.

```
Error: Failed to get existing workspaces: S3 bucket does not exist.
```

**Fix:** Create the backend resources using the commands in
[First-Time Setup -- Step 3](#3-create-the-terraform-state-backend), or verify
your AWS credentials have `s3:*` and `dynamodb:*` permissions on the state
resources.

### `terraform plan` fails with "allowed_cidr_blocks must contain at least one CIDR block"

The `allowed_cidr_blocks` variable is required but not set in your `.tfvars` file.

```
Error: Invalid value for variable "allowed_cidr_blocks"
  allowed_cidr_blocks must contain at least one CIDR block.
```

**Fix:** Add `allowed_cidr_blocks` to your `.tfvars` file:

```hcl
# Open to all (staging)
allowed_cidr_blocks = ["0.0.0.0/0"]

# Or restrict to a specific IP range
allowed_cidr_blocks = ["203.0.113.50/32"]
```

### `terraform plan` fails with certificate ARN error

If you see an error referencing the ACM certificate, the ARN is either a
placeholder or the certificate has not been validated yet.

```
Error: error describing ACM Certificate (arn:aws:acm:...REPLACE_ME): certificate not found
```

**Fix:**
1. Verify the certificate exists: `aws acm list-certificates --region us-east-1`
2. Check its status: `aws acm describe-certificate --certificate-arn <ARN> --region us-east-1`
3. If status is `PENDING_VALIDATION`, complete the DNS validation (see
   [Obtaining an ACM Certificate](#obtaining-an-acm-certificate))
4. If the ARN still contains `REPLACE_ME` or `YOUR_AWS_ACCOUNT_ID`, update it
   with the real ARN

### `terraform plan` fails with missing `TF_VAR_*` environment variable

Terraform cannot find a required secret variable.

```
Error: No value for required variable "db_password"
```

**Fix:** Export the missing variable before running terraform:

```bash
export TF_VAR_db_password="$(openssl rand -base64 24)"
```

See the [Secret Variables](#secret-variables-set-as-environment-variables----never-in-tfvars-files)
table for all four required secrets and how to generate them.

### `terraform apply` fails with "BucketAlreadyExists" for S3

S3 bucket names are globally unique. If production already created a bucket
named `selfpublisherforge-assets`, staging cannot use the same name.

```
Error: creating Amazon S3 Bucket: BucketAlreadyExists
```

**Fix:** Override the bucket names in your staging `.tfvars`:

```hcl
assets_bucket_name   = "selfpublisherforge-assets-staging"
backups_bucket_name  = "selfpublisherforge-backups-staging"
frontend_bucket_name = "selfpublisherforge-frontend-staging"
```

### `terraform apply` times out on ECS service creation

ECS services can take several minutes to stabilize. If tasks fail health checks
repeatedly, Terraform will time out.

**Fix:**
1. Check the ECS service events: `aws ecs describe-services --cluster selfpublisherforge-<env> --services selfpublisherforge-api-<env>`
2. Check CloudWatch logs: `aws logs tail /ecs/selfpublisherforge-api-<env> --follow`
3. Common causes: Docker image not pushed to ECR, incorrect container port,
   health check path returns non-200, insufficient task memory

### State lock error ("Error acquiring the state lock")

Another Terraform process (or a previous crashed run) is holding the DynamoDB lock.

```
Error: Error acquiring the state lock
```

**Fix:**
1. Wait for any other `terraform apply` to finish
2. If no other process is running, force-unlock:
   `terraform force-unlock <LOCK_ID>`
   (the lock ID is shown in the error message)

### CloudFront returns 403 after deploy

CloudFront is not able to reach the S3 origin or the ALB origin.

**Fix:**
1. Verify the frontend S3 bucket has objects: `aws s3 ls s3://selfpublisherforge-frontend-<env>/`
2. Ensure the S3 bucket policy allows CloudFront OAI access (Terraform manages this)
3. Invalidate the CloudFront cache: `aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"`

---

## Outputs

After a successful `terraform apply`, useful values are printed. Key outputs include:

| Output | Description |
|--------|-------------|
| `alb_dns_name` | ALB DNS name (for staging access or DNS CNAME targets) |
| `cloudfront_domain_name` | CloudFront distribution domain |
| `cloudfront_distribution_id` | CloudFront ID (for cache invalidation in CI/CD) |
| `rds_endpoint` | RDS PostgreSQL endpoint (host:port) |
| `redis_endpoint` | ElastiCache Redis endpoint |
| `ecr_api_repository_url` | ECR URL for API Docker images |
| `ecr_frontend_repository_url` | ECR URL for Frontend Docker images |
| `opensearch_endpoint` | OpenSearch domain endpoint |
| `opensearch_dashboard_endpoint` | OpenSearch Dashboards URL |

Retrieve outputs any time with:

```bash
terraform output

# Get a specific output
terraform output alb_dns_name

# Get outputs in JSON (useful for scripts and CI/CD)
terraform output -json
```

---

## Environment Comparison

| Aspect | Staging | Production |
|--------|---------|------------|
| ECS task count | 1 per service | 2+ per service (auto-scaled) |
| API CPU / Memory | 256 / 512 MiB | 512 / 1024 MiB |
| Worker CPU / Memory | 256 / 512 MiB | 512 / 1024 MiB |
| RDS instance | db.t3.small (single-AZ) | db.t3.medium (Multi-AZ) |
| RDS storage | 20-50 GB | 50-200 GB |
| RDS backups | 3 days | 7 days |
| Redis | cache.t3.small | cache.t3.medium |
| Log retention | 14 days | 30 days |
| Domain | Optional (ALB DNS fallback) | Required (custom domain) |
| SSL certificate | Optional | Required |
| SNS alarms | Optional | Required |
| Estimated monthly cost | ~$80-120 USD | ~$250-400 USD |

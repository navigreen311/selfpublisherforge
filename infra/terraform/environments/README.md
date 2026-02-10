# Terraform Environment Configurations

This directory contains per-environment variable override files (`.tfvars`) used
to deploy the **SelfPublisherForge** infrastructure into AWS.

| File | Purpose |
|------|---------|
| `production.tfvars` | Production environment overrides — larger instances, Multi-AZ RDS, longer log retention |
| `staging.tfvars` | Staging environment overrides — smaller instances, single-AZ RDS, shorter retention |

---

## Variables That Require Configuration

Before deploying either environment, every variable listed below must be set.
Variables are split into two categories: **in-file values** (edited directly in
the `.tfvars` file) and **environment variables** (exported in your shell).

### In-File Values

| Variable | Required In | How to Obtain |
|----------|-------------|---------------|
| `domain_name` | production (optional staging) | Your registered domain name, e.g. `selfpublisherforge.com` |
| `certificate_arn` | production (optional staging) | AWS ACM certificate ARN — see [Obtaining an ACM Certificate](#obtaining-an-acm-certificate) |
| `alarm_sns_topic_arn` | production | AWS SNS topic ARN — see [Creating an SNS Topic](#creating-an-sns-topic) |

### Environment Variables (Secrets)

These **must never** be committed to version control. Export them in your shell
before running `terraform plan` or `terraform apply`.

| Environment Variable | Description | How to Generate |
|----------------------|-------------|-----------------|
| `TF_VAR_db_username` | RDS PostgreSQL master username | Choose a username, e.g. `spf_admin` |
| `TF_VAR_db_password` | RDS PostgreSQL master password | `openssl rand -base64 24` |
| `TF_VAR_jwt_secret_key` | JWT signing secret for the API | `openssl rand -hex 32` |
| `TF_VAR_app_secret_key` | Django `SECRET_KEY` | `openssl rand -hex 50` |

> **Important:** Use different secret values for staging and production to
> maintain security isolation between environments.

---

## Obtaining an ACM Certificate

CloudFront requires the certificate to be in **us-east-1** regardless of your
application region.

```bash
# Step 1 — Request a certificate (with wildcard for subdomains)
aws acm request-certificate \
  --domain-name selfpublisherforge.com \
  --subject-alternative-names "*.selfpublisherforge.com" \
  --validation-method DNS \
  --region us-east-1

# The output includes a CertificateArn. Save it.

# Step 2 — Retrieve the DNS validation records
aws acm describe-certificate \
  --certificate-arn <CertificateArn> \
  --region us-east-1 \
  --query 'Certificate.DomainValidationOptions[].ResourceRecord'

# Step 3 — Create the CNAME record(s) shown above in your DNS provider
#          (Route 53, Cloudflare, Namecheap, etc.)

# Step 4 — Wait for the certificate to validate (5-30 minutes)
aws acm wait certificate-validated \
  --certificate-arn <CertificateArn> \
  --region us-east-1

# Step 5 — Copy the CertificateArn into the certificate_arn field in your tfvars file
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
# Step 1 — Create the topic
aws sns create-topic \
  --name selfpublisherforge-production-alarms \
  --region us-east-1

# The output includes a TopicArn. Save it.

# Step 2 — Subscribe your email
aws sns subscribe \
  --topic-arn <TopicArn> \
  --protocol email \
  --notification-endpoint ops-team@example.com \
  --region us-east-1

# Step 3 — Check your inbox and click the confirmation link from AWS.

# Step 4 — (Optional) Add a PagerDuty / Slack / OpsGenie webhook
aws sns subscribe \
  --topic-arn <TopicArn> \
  --protocol https \
  --notification-endpoint https://events.pagerduty.com/integration/<key>/enqueue

# Step 5 — Paste the TopicArn into the alarm_sns_topic_arn field in production.tfvars
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

## Pre-Deployment Checklist

Run through this checklist before your first deployment to either environment.

### One-Time AWS Account Setup

- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Terraform >= 1.6.0 installed (`terraform version`)
- [ ] S3 state bucket exists: `selfpublisherforge-terraform-state`
- [ ] DynamoDB lock table exists: `selfpublisherforge-terraform-locks`

### Per-Environment Checklist

- [ ] All TODO placeholders in the `.tfvars` file have been replaced with real values
- [ ] `TF_VAR_db_username` exported
- [ ] `TF_VAR_db_password` exported (>= 16 characters)
- [ ] `TF_VAR_jwt_secret_key` exported
- [ ] `TF_VAR_app_secret_key` exported
- [ ] ACM certificate is in **Issued** status (for production, or staging with custom domain)
- [ ] SNS topic subscription is **Confirmed** (for production)
- [ ] `terraform init` has been run

### Production-Specific Checks

- [ ] `domain_name` is set to the real production domain
- [ ] `certificate_arn` points to a validated ACM certificate in us-east-1
- [ ] `alarm_sns_topic_arn` points to an active SNS topic with confirmed subscribers
- [ ] `db_multi_az` is `true`
- [ ] DNS records are ready to be created post-deploy

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
# Export secrets (use your real, securely stored values — not random ones)
export TF_VAR_db_username="spf_admin"
export TF_VAR_db_password="<your-secure-password>"
export TF_VAR_jwt_secret_key="<your-jwt-secret>"
export TF_VAR_app_secret_key="<your-django-secret>"

# Preview changes — ALWAYS review the plan before applying to production
terraform plan -var-file=environments/production.tfvars

# Apply (with manual approval)
terraform apply -var-file=environments/production.tfvars
```

> **Tip:** For CI/CD pipelines, store the four secret values in your pipeline's
> secret manager (GitHub Actions secrets, AWS Secrets Manager, etc.) and inject
> them as `TF_VAR_*` environment variables at runtime.

---

## Outputs

After a successful `terraform apply`, useful values are printed. Common outputs:

- ALB DNS name (for staging access or DNS CNAME targets)
- CloudFront distribution domain
- RDS endpoint
- Redis endpoint
- ECR repository URLs (for Docker image pushes)

Retrieve outputs any time with:

```bash
terraform output
```

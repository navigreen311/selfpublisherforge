# W16: Terraform — Extract Secrets to AWS SSM/Secrets Manager

## Files to modify
- `infra/terraform/variables.tf` or similar — Remove plaintext defaults
- `infra/terraform/terraform.tfvars` — Remove plaintext passwords
- `infra/terraform/secrets.tf` — NEW: AWS Secrets Manager resources

## Task

### 1. Read current Terraform files

Read all .tf and .tfvars files in `infra/terraform/` to identify plaintext secrets (passwords, API keys, tokens).

### 2. Create secrets.tf

Move all secrets to AWS Secrets Manager:

```hcl
resource "aws_secretsmanager_secret" "db_password" {
  name        = "${var.project_name}-${var.environment}-db-password"
  description = "RDS database master password"
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name        = "${var.project_name}-${var.environment}-jwt-secret"
  description = "JWT signing secret"
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = var.jwt_secret_key
}

# ... repeat for other secrets (Redis password, Stripe keys, etc.)
```

### 3. Update variable declarations

Mark sensitive variables:
```hcl
variable "db_password" {
  type      = string
  sensitive = true
}

variable "jwt_secret_key" {
  type      = string
  sensitive = true
}
```

### 4. Remove plaintext values from tfvars

Replace plaintext passwords in terraform.tfvars with placeholder comments:
```hcl
# db_password = "SET_VIA_TF_VAR_db_password_ENV_VARIABLE"
# jwt_secret_key = "SET_VIA_TF_VAR_jwt_secret_key_ENV_VARIABLE"
```

### 5. Update references

Update any Terraform resources that reference these secrets to use the Secrets Manager ARN instead of direct values where applicable (e.g., ECS task definitions).

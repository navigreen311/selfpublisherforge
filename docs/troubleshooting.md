# Troubleshooting Guide

This guide covers common issues you may encounter when developing or deploying SelfPublisherForge. Each section describes the symptoms, how to diagnose the problem, and the recommended solution.

---

## Table of Contents

1. [Database Connection Errors](#1-database-connection-errors)
2. [Redis Connection Errors](#2-redis-connection-errors)
3. [Elasticsearch Errors](#3-elasticsearch-errors)
4. [Celery Worker Issues](#4-celery-worker-issues)
5. [S3 / Storage Errors](#5-s3--storage-errors)
6. [Auth Issues](#6-auth-issues)
7. [Stripe / Billing](#7-stripe--billing)
8. [Email Delivery](#8-email-delivery)
9. [Frontend Build Errors](#9-frontend-build-errors)
10. [Docker Compose](#10-docker-compose)

---

## 1. Database Connection Errors

### 1a. PostgreSQL not running

**Symptoms:**
- Application fails to start with `ConnectionRefusedError` or `Connection refused` on port 5432.
- Logs show `asyncpg.exceptions.ConnectionDoesNotExistError` or `sqlalchemy.exc.OperationalError`.

**Diagnosis:**
```bash
# Check if PostgreSQL is running (Docker)
docker compose ps postgres

# Check if port 5432 is open
# Linux/macOS:
ss -tlnp | grep 5432
# Windows:
netstat -an | findstr 5432

# Check PostgreSQL container logs
docker compose logs postgres
```

**Solution:**
```bash
# Start PostgreSQL via Docker Compose
docker compose up -d postgres

# If the container starts but is unhealthy, check the logs
docker compose logs --tail=50 postgres

# If running locally (without Docker), start the service:
# Linux:
sudo systemctl start postgresql
# macOS (Homebrew):
brew services start postgresql@16
# Windows:
net start postgresql-x64-16
```

### 1b. Wrong credentials

**Symptoms:**
- `password authentication failed for user "postgres"`.
- `FATAL: role "postgres" does not exist`.

**Diagnosis:**
```bash
# Verify your DATABASE_URL in .env matches the actual database credentials
grep DATABASE_URL backend/.env

# Test the connection directly
psql "postgresql://postgres:postgres@localhost:5432/selfpublisherforge"
```

**Solution:**
1. Ensure `DATABASE_URL` in `backend/.env` matches the credentials in `docker-compose.yml` (default: `postgres:postgres`).
2. If you changed `POSTGRES_PASSWORD` in `docker-compose.yml`, update `DATABASE_URL` to match.
3. If the database was created with different credentials, recreate it:
   ```bash
   docker compose down -v  # WARNING: deletes all data
   docker compose up -d postgres
   ```

### 1c. Migration issues

**Symptoms:**
- `alembic.util.exc.CommandError: Can't locate revision identified by ...`
- `sqlalchemy.exc.ProgrammingError: relation "..." does not exist`
- Application starts but returns 500 errors on database queries.

**Diagnosis:**
```bash
# Check current migration head
cd backend && alembic current

# List migration history
alembic history --verbose

# Check if the database has the alembic_version table
psql "postgresql://postgres:postgres@localhost:5432/selfpublisherforge" \
  -c "SELECT * FROM alembic_version;"
```

**Solution:**
```bash
# Run all pending migrations
cd backend && alembic upgrade head

# If migrations are out of sync, stamp the current state and re-run
alembic stamp head
alembic upgrade head

# Nuclear option: reset the database entirely (dev only!)
docker compose down -v
docker compose up -d postgres
cd backend && alembic upgrade head
```

---

## 2. Redis Connection Errors

### 2a. Redis not running

**Symptoms:**
- `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379. Connection refused.`
- Application starts but caching, rate limiting, and WebSocket features fail.
- Celery workers refuse to start (broker connection failed).

**Diagnosis:**
```bash
# Check if Redis is running (Docker)
docker compose ps redis

# Ping Redis directly
redis-cli ping
# Expected response: PONG

# Check Redis container logs
docker compose logs redis
```

**Solution:**
```bash
# Start Redis via Docker Compose
docker compose up -d redis

# If running locally:
# Linux:
sudo systemctl start redis
# macOS (Homebrew):
brew services start redis
# Windows: start the Redis service or run redis-server directly
```

### 2b. Wrong Redis URL

**Symptoms:**
- Connection errors pointing to an unexpected host or port.
- Celery connects but tasks never execute (wrong database number).

**Diagnosis:**
```bash
# Verify all Redis URLs in .env
grep REDIS backend/.env
# Expected:
#   REDIS_URL=redis://localhost:6379/0
#   CELERY_BROKER_URL=redis://localhost:6379/1
#   CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

**Solution:**
1. Ensure `REDIS_URL`, `CELERY_BROKER_URL`, and `CELERY_RESULT_BACKEND` all point to the same Redis instance but use **different database numbers** (0, 1, 2 respectively).
2. If running Redis in Docker, the hostname inside the Docker network is `redis` (not `localhost`). The backend service in Docker Compose should use `redis://redis:6379/0`.
3. For local development without Docker, use `redis://localhost:6379/0`.

---

## 3. Elasticsearch Errors

### 3a. Elasticsearch not running

**Symptoms:**
- `elasticsearch.exceptions.ConnectionError: ConnectionError(...) caused by: ConnectionRefusedError`
- Knowledge Vault and Market Intelligence search endpoints return 500 errors.

**Diagnosis:**
```bash
# Check if Elasticsearch is running
docker compose ps elasticsearch

# Test the connection
curl -s http://localhost:9200

# Check container logs (ES is memory-hungry and often fails to start)
docker compose logs elasticsearch
```

**Solution:**
```bash
# Start Elasticsearch
docker compose up -d elasticsearch

# If ES fails to start due to memory, increase Docker memory allocation
# (ES requires at least 1GB; 2GB recommended)

# On Linux, if you see "max virtual memory areas vm.max_map_count [65530] is too low":
sudo sysctl -w vm.max_map_count=262144
# To persist across reboots, add to /etc/sysctl.conf:
#   vm.max_map_count=262144
```

### 3b. Cluster health red / yellow

**Symptoms:**
- Search queries time out or return partial results.
- `curl http://localhost:9200/_cluster/health` shows `"status": "red"`.

**Diagnosis:**
```bash
# Check cluster health
curl -s http://localhost:9200/_cluster/health?pretty

# Check which indices have problems
curl -s http://localhost:9200/_cat/indices?v

# Check unassigned shards
curl -s http://localhost:9200/_cat/shards?v | grep UNASSIGNED
```

**Solution:**
```bash
# For development (single-node), a yellow status is normal and harmless.
# Yellow means replicas are unassigned, which is expected with one node.

# For a red status, check disk space first:
df -h  # Linux/macOS
wmic logicaldisk get size,freespace,caption  # Windows

# If disk space is low, clear old indices:
curl -X DELETE http://localhost:9200/old-index-name

# If indices are corrupted, recreate them:
curl -X DELETE http://localhost:9200/selfpublisherforge-*
# Then restart the application to re-create indices
```

### 3c. Index does not exist

**Symptoms:**
- `elasticsearch.exceptions.NotFoundError: index_not_found_exception`
- Search features return empty results immediately after a fresh setup.

**Diagnosis:**
```bash
# List all indices
curl -s http://localhost:9200/_cat/indices?v
```

**Solution:**
```bash
# Re-index by hitting the application's reindex endpoint or running:
cd backend && python -m app.scripts.create_indices

# Or restart the backend service, which creates indices on startup
docker compose restart backend
```

---

## 4. Celery Worker Issues

### 4a. Workers not starting

**Symptoms:**
- `celery-worker` container exits immediately.
- `Error: No module named 'app.tasks'` in the logs.
- `kombu.exceptions.OperationalError: [Errno 111] Connection refused` (broker unreachable).

**Diagnosis:**
```bash
# Check worker status
docker compose ps celery-worker

# Check worker logs
docker compose logs --tail=100 celery-worker

# Verify Redis (broker) is running
docker compose ps redis
redis-cli ping
```

**Solution:**
```bash
# Ensure Redis is running first
docker compose up -d redis

# Restart workers
docker compose restart celery-worker celery-beat

# If the module import fails, verify the backend code is mounted correctly
docker compose exec celery-worker ls /app/app/tasks/

# For local development without Docker:
cd backend && celery -A app.tasks worker -l info -c 4
```

### 4b. Tasks stuck in queue

**Symptoms:**
- Background tasks (AI generation, exports, email sending) never complete.
- Flower dashboard (http://localhost:5555) shows tasks in "PENDING" state indefinitely.
- Redis queue length keeps growing.

**Diagnosis:**
```bash
# Check queue length
redis-cli -n 1 LLEN celery

# Check active workers
cd backend && celery -A app.tasks inspect active

# Check if workers are consuming tasks
cd backend && celery -A app.tasks inspect reserved

# Check Flower for task states
curl -s http://localhost:5555/api/tasks | python -m json.tool
```

**Solution:**
```bash
# Restart workers to pick up stuck tasks
docker compose restart celery-worker

# If tasks are truly stuck, purge the queue (WARNING: deletes all pending tasks)
cd backend && celery -A app.tasks purge -f

# Increase worker concurrency if tasks are bottlenecked
# Edit docker-compose.yml: change "-c 4" to "-c 8" in the celery-worker command

# Check if a specific task type is failing repeatedly
docker compose logs celery-worker 2>&1 | grep "Task .* raised"
```

### 4c. Celery Beat not scheduling

**Symptoms:**
- Periodic tasks (scheduled reports, data syncs) do not execute.
- Flower shows no scheduled tasks.

**Diagnosis:**
```bash
# Check beat container
docker compose ps celery-beat
docker compose logs --tail=50 celery-beat
```

**Solution:**
```bash
# Restart beat scheduler
docker compose restart celery-beat

# If beat's schedule file is corrupted, remove it and restart:
docker compose exec celery-beat rm -f /app/celerybeat-schedule
docker compose restart celery-beat
```

---

## 5. S3 / Storage Errors

### 5a. Wrong AWS credentials

**Symptoms:**
- `botocore.exceptions.ClientError: An error occurred (InvalidAccessKeyId)`
- `botocore.exceptions.NoCredentialsError: Unable to locate credentials`
- File uploads return 500 errors.

**Diagnosis:**
```bash
# Verify credentials are set
grep AWS_ backend/.env

# Test credentials with the AWS CLI
aws sts get-caller-identity
```

**Solution:**
1. Ensure `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `backend/.env` are valid.
2. If using Cloudflare R2, make sure you are using R2-specific access keys (not your main AWS keys).
3. Generate new keys if the existing ones are invalid:
   - AWS: IAM Console > Users > Security Credentials > Create Access Key
   - R2: Cloudflare Dashboard > R2 > Manage R2 API Tokens

### 5b. Bucket not found

**Symptoms:**
- `botocore.exceptions.ClientError: An error occurred (NoSuchBucket)`
- `The specified bucket does not exist`

**Diagnosis:**
```bash
# Verify bucket name in .env
grep S3_BUCKET backend/.env

# List your buckets
aws s3 ls
```

**Solution:**
```bash
# Create the bucket
aws s3 mb s3://selfpublisherforge-assets --region us-east-1

# Or update S3_BUCKET in .env to match an existing bucket name
```

### 5c. Permission denied (AccessDenied)

**Symptoms:**
- `botocore.exceptions.ClientError: An error occurred (AccessDenied) when calling PutObject`
- Uploads work but downloads fail (or vice versa).

**Diagnosis:**
```bash
# Test specific operations
aws s3 ls s3://selfpublisherforge-assets/
aws s3 cp test.txt s3://selfpublisherforge-assets/test.txt
aws s3 cp s3://selfpublisherforge-assets/test.txt ./downloaded.txt
```

**Solution:**
1. Ensure the IAM user/role has the following S3 permissions on the bucket:
   - `s3:GetObject`
   - `s3:PutObject`
   - `s3:DeleteObject`
   - `s3:ListBucket`
2. Check the bucket policy does not explicitly deny access.
3. If using R2, ensure the API token has the "Object Read & Write" permission.

---

## 6. Auth Issues

### 6a. Token expired

**Symptoms:**
- API returns `401 Unauthorized` with `{"detail": "Token has expired"}`.
- User is logged out unexpectedly.

**Diagnosis:**
- Check the `ACCESS_TOKEN_EXPIRE_MINUTES` value in `backend/.env` (default: 15 minutes).
- Decode the JWT token at https://jwt.io to inspect the `exp` claim.

**Solution:**
1. The frontend should automatically refresh tokens using the refresh token endpoint (`POST /api/v1/auth/refresh`).
2. If refresh tokens are also expired, the user must log in again.
3. For development, you can increase `ACCESS_TOKEN_EXPIRE_MINUTES` (e.g., to 60) and `REFRESH_TOKEN_EXPIRE_DAYS` (e.g., to 30).

### 6b. Invalid token / signature verification failed

**Symptoms:**
- `401 Unauthorized` with `{"detail": "Could not validate credentials"}`.
- Tokens issued before a server restart are rejected.

**Diagnosis:**
```bash
# Check if SECRET_KEY is consistent
grep SECRET_KEY backend/.env
```

**Solution:**
1. If `SECRET_KEY` was changed or is still the placeholder value, all existing tokens are invalidated.
2. Set a permanent `SECRET_KEY` and do not change it between deployments:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```
3. After changing the secret, all users must log in again.

### 6c. MFA (Multi-Factor Authentication) problems

**Symptoms:**
- User cannot complete MFA verification.
- TOTP codes are consistently rejected.

**Diagnosis:**
- Verify the server's clock is accurate (TOTP is time-based and allows ~30 second drift).
- Check if the user's authenticator app clock is synced.

**Solution:**
1. Ensure server time is synchronized:
   ```bash
   # Check server time
   date
   # Sync with NTP (Linux)
   sudo timedatectl set-ntp true
   ```
2. If the user's TOTP secret is corrupted, an admin can reset MFA for the user through the admin panel or directly in the database.
3. Provide the user with their backup recovery codes if they have them.

### 6d. OAuth login fails (Google / GitHub)

**Symptoms:**
- "Sign in with Google/GitHub" redirects to an error page.
- `redirect_uri_mismatch` error from the OAuth provider.

**Diagnosis:**
```bash
# Verify OAuth credentials are set
grep -E "GOOGLE_|GITHUB_" backend/.env
```

**Solution:**
1. Ensure `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GITHUB_CLIENT_ID`, and `GITHUB_CLIENT_SECRET` are set in `backend/.env`.
2. Verify the redirect URIs match exactly:
   - Google Cloud Console: Authorized redirect URIs must include `http://localhost:3000/auth/google/callback` (dev) or your production URL.
   - GitHub Developer Settings: Authorization callback URL must match `GITHUB_REDIRECT_URI`.
3. For local development, Google requires `http://localhost` (not `127.0.0.1`).

---

## 7. Stripe / Billing

### 7a. Webhook failures

**Symptoms:**
- Stripe dashboard shows webhook deliveries failing (HTTP 400 or 500).
- Subscriptions are created in Stripe but not reflected in the app.
- Logs show `stripe.error.SignatureVerificationError`.

**Diagnosis:**
```bash
# Check webhook secret
grep STRIPE_WEBHOOK_SECRET backend/.env

# Test webhook connectivity locally using the Stripe CLI
stripe listen --forward-to localhost:8000/api/v1/billing/webhook

# View recent webhook events
stripe events list --limit 5
```

**Solution:**
1. For local development, install and use the [Stripe CLI](https://stripe.com/docs/stripe-cli):
   ```bash
   stripe listen --forward-to localhost:8000/api/v1/billing/webhook
   # Copy the webhook signing secret (whsec_...) printed by the CLI
   # Update STRIPE_WEBHOOK_SECRET in backend/.env
   ```
2. For production, ensure the webhook endpoint URL in the Stripe Dashboard matches your API URL (`https://yourdomain.com/api/v1/billing/webhook`).
3. Verify `STRIPE_WEBHOOK_SECRET` matches the signing secret shown in the Stripe Dashboard under Webhooks > your endpoint > Signing secret.

### 7b. Missing Stripe Price IDs

**Symptoms:**
- Subscription page shows no pricing tiers or returns errors.
- `stripe.error.InvalidRequestError: No such price: 'price_XXXXXXXXXXXXX'`

**Diagnosis:**
```bash
# Check price IDs in .env
grep STRIPE_PRICE backend/.env

# Verify prices exist in Stripe
stripe prices list --limit 10
```

**Solution:**
1. Create products and prices in the [Stripe Dashboard](https://dashboard.stripe.com/products) or via the CLI:
   ```bash
   stripe products create --name "Starter" --description "Starter plan"
   stripe prices create --product prod_XXX --unit-amount 999 --currency usd --recurring-interval month
   ```
2. Copy the `price_XXXXXXXXXXXXX` IDs to `backend/.env`.
3. Ensure you are using Price IDs (not Product IDs) -- they start with `price_`.

### 7c. Test mode vs. live mode mismatch

**Symptoms:**
- Payments work in development but fail in production (or vice versa).
- `stripe.error.AuthenticationError: Invalid API Key provided: sk_test_****`

**Diagnosis:**
```bash
# Check which mode the key belongs to
grep STRIPE_SECRET_KEY backend/.env
# Test keys start with sk_test_
# Live keys start with sk_live_
```

**Solution:**
1. Development must use `sk_test_` keys; production must use `sk_live_` keys.
2. Webhook secrets are also mode-specific -- each endpoint has its own signing secret.
3. Price IDs created in test mode are not valid in live mode (and vice versa). Create separate products for each mode.

---

## 8. Email Delivery

### 8a. SendGrid API key invalid

**Symptoms:**
- `sendgrid.helpers.mail.SendGridException: HTTP Error 401 Unauthorized`
- Password reset and notification emails are never delivered.

**Diagnosis:**
```bash
# Verify the API key is set
grep SENDGRID_API_KEY backend/.env

# Test the key directly
curl -X GET https://api.sendgrid.com/v3/mail/send \
  -H "Authorization: Bearer YOUR_SENDGRID_API_KEY_HERE" \
  -H "Content-Type: application/json"
# A 401 response means the key is invalid
```

**Solution:**
1. Generate a new API key at [SendGrid Settings](https://app.sendgrid.com/settings/api_keys).
2. Ensure the key has at minimum the "Mail Send" permission.
3. Update `SENDGRID_API_KEY` in `backend/.env`.
4. Verify the sender email (`FROM_EMAIL`) is authenticated in SendGrid (Settings > Sender Authentication).

### 8b. SMTP connection refused (fallback)

**Symptoms:**
- `smtplib.SMTPConnectError: [Errno 111] Connection refused`
- `smtplib.SMTPAuthenticationError: (535, 'Authentication failed')`

**Diagnosis:**
```bash
# Check SMTP settings
grep SMTP backend/.env

# Test SMTP connectivity
# Linux/macOS:
nc -zv smtp.example.com 587
# Windows:
Test-NetConnection -ComputerName smtp.example.com -Port 587
```

**Solution:**
1. Verify `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, and `SMTP_PASS` are all correctly set in `backend/.env`.
2. Common SMTP configurations:
   - **Gmail**: `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, use an App Password (not your regular password).
   - **Amazon SES**: `SMTP_HOST=email-smtp.us-east-1.amazonaws.com`, `SMTP_PORT=587`, use SMTP credentials from SES.
3. If you do not need SMTP fallback, leave `SMTP_HOST` unset (commented out) and rely on SendGrid.

### 8c. Emails landing in spam

**Symptoms:**
- Emails are sent successfully (200 response from SendGrid) but never arrive in the inbox.
- Emails arrive but are marked as spam.

**Solution:**
1. Set up domain authentication in SendGrid (SPF, DKIM, DMARC records).
2. Ensure `FROM_EMAIL` uses a domain you have authenticated.
3. Avoid using free email domains (gmail.com, yahoo.com) as the sender.
4. Check your SendGrid reputation at SendGrid Dashboard > Suppressions.

---

## 9. Frontend Build Errors

### 9a. Missing environment variables

**Symptoms:**
- Build fails with `NEXT_PUBLIC_API_URL is not defined`.
- App loads but API calls go to `undefined/api/v1/...`.

**Diagnosis:**
```bash
# Check if .env.local exists
ls frontend/.env.local

# Verify required variables
cat frontend/.env.local
```

**Solution:**
```bash
# Copy the example and fill in values
cp frontend/.env.example frontend/.env.local

# Required variables:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000
# NEXT_PUBLIC_APP_URL=http://localhost:3000
# NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### 9b. TypeScript errors

**Symptoms:**
- `Type error: Property 'X' does not exist on type 'Y'`
- Build fails at the type-checking step.
- Red squiggles in your editor that do not match the actual runtime behavior.

**Diagnosis:**
```bash
# Run the TypeScript compiler directly
cd frontend && npx tsc --noEmit

# Check TypeScript version
npx tsc --version
```

**Solution:**
```bash
# Fix auto-fixable issues
cd frontend && npx tsc --noEmit 2>&1 | head -50

# If types are stale, regenerate them
cd frontend && npm run generate-types  # if this script exists

# If node_modules types are corrupted, clean and reinstall
rm -rf frontend/node_modules frontend/.next
cd frontend && npm install
```

### 9c. Dependency issues / npm install failures

**Symptoms:**
- `npm ERR! ERESOLVE unable to resolve dependency tree`
- `Module not found: Can't resolve 'package-name'`
- Build succeeds locally but fails in CI/Docker.

**Diagnosis:**
```bash
# Check Node.js version (project may require a specific version)
node --version

# Check for lockfile consistency
cd frontend && npm ci  # Strict install from lockfile
```

**Solution:**
```bash
# Clean install from lockfile (preferred for CI consistency)
cd frontend
rm -rf node_modules .next
npm ci

# If ERESOLVE errors persist, check for peer dependency conflicts
npm install --legacy-peer-deps

# Ensure Node.js version matches the project requirement
# Check .nvmrc or engines field in package.json
nvm use  # if using nvm
```

---

## 10. Docker Compose

### 10a. Services not starting

**Symptoms:**
- `docker compose up` exits immediately.
- Services show as "Exited (1)" in `docker compose ps`.

**Diagnosis:**
```bash
# Check status of all services
docker compose ps

# Check logs for the failing service
docker compose logs <service-name>

# Validate docker-compose.yml syntax
docker compose config
```

**Solution:**
```bash
# Rebuild images after code or Dockerfile changes
docker compose build --no-cache

# Start with fresh state
docker compose down
docker compose up -d

# If a specific service fails, start it in isolation to see errors
docker compose up backend
```

### 10b. Port conflicts

**Symptoms:**
- `Bind for 0.0.0.0:8000 failed: port is already allocated`
- `Error starting userland proxy: listen tcp4 0.0.0.0:5432: bind: address already in use`

**Diagnosis:**
```bash
# Find what is using the port
# Linux/macOS:
lsof -i :8000
# Windows:
netstat -ano | findstr :8000
```

**Solution:**
1. Stop the conflicting process:
   ```bash
   # Linux/macOS:
   kill -9 <PID>
   # Windows:
   taskkill /PID <PID> /F
   ```
2. Or change the port mapping in `docker-compose.yml`:
   ```yaml
   ports:
     - "8001:8000"  # Map to a different host port
   ```
3. Common conflicts:
   | Port | Service | Typical Conflict |
   |------|---------|-----------------|
   | 3000 | Frontend | Another Node.js dev server |
   | 5432 | PostgreSQL | Locally installed PostgreSQL |
   | 6379 | Redis | Locally installed Redis |
   | 8000 | Backend | Another Python/FastAPI server |
   | 9200 | Elasticsearch | Locally installed ES |

### 10c. Volume permissions

**Symptoms:**
- `PermissionError: [Errno 13] Permission denied: '/app/...'`
- Elasticsearch fails with `java.nio.file.AccessDeniedException: /usr/share/elasticsearch/data`
- PostgreSQL fails with `initdb: could not change permissions of directory`

**Diagnosis:**
```bash
# Check volume ownership
docker compose exec backend ls -la /app
docker compose exec postgres ls -la /var/lib/postgresql/data
```

**Solution:**
```bash
# Fix Elasticsearch data directory permissions (common on Linux)
sudo chown -R 1000:1000 /var/lib/docker/volumes/*esdata*

# Or set the correct user in docker-compose.yml for ES:
# elasticsearch:
#   user: "1000:1000"

# Nuclear option: remove all volumes and start fresh
docker compose down -v
docker compose up -d
```

### 10d. Docker running out of disk space

**Symptoms:**
- `no space left on device` errors during build or runtime.
- Containers start but crash with write errors.

**Diagnosis:**
```bash
# Check Docker disk usage
docker system df

# List dangling images and stopped containers
docker images -f "dangling=true"
docker ps -a --filter "status=exited"
```

**Solution:**
```bash
# Remove unused containers, networks, images, and build cache
docker system prune -a --volumes

# Or selectively clean up
docker container prune   # Remove stopped containers
docker image prune -a    # Remove unused images
docker volume prune      # Remove unused volumes
docker builder prune     # Remove build cache
```

### 10e. Health checks failing

**Symptoms:**
- Services show as "unhealthy" in `docker compose ps`.
- Dependent services (e.g., backend) refuse to start because upstream is unhealthy.

**Diagnosis:**
```bash
# Check health status
docker compose ps

# Inspect a specific container's health
docker inspect --format='{{json .State.Health}}' selfpublisherforge-backend-1

# Run the health check command manually inside the container
docker compose exec backend curl -f http://localhost:8000/health
docker compose exec postgres pg_isready -U postgres -d selfpublisherforge
docker compose exec redis redis-cli ping
```

**Solution:**
1. If a service is starting slowly, increase the `start_period` in its health check config.
2. If the health check command itself is wrong, fix it in `docker-compose.yml`.
3. If a dependency is unhealthy, fix that service first -- dependent services will start automatically once dependencies are healthy.

---

## Quick Reference: Service Ports

| Service | Default Port | Health Check |
|---------|-------------|--------------|
| Backend (FastAPI) | 8000 | `GET /health` |
| Frontend (Next.js) | 3000 | `GET /` |
| PostgreSQL | 5432 | `pg_isready` |
| Redis | 6379 | `redis-cli ping` |
| Elasticsearch | 9200 | `GET /_cluster/health` |
| Celery Flower | 5555 | `GET /healthcheck` |
| Prometheus | 9090 | `GET /-/healthy` |
| Grafana | 3001 | `GET /api/health` |
| Alertmanager | 9093 | `GET /-/healthy` |

---

## Quick Reference: Useful Commands

```bash
# Start everything
docker compose up -d

# View all logs
docker compose logs -f

# Restart a single service
docker compose restart backend

# Run database migrations
docker compose exec backend alembic upgrade head

# Open a shell inside the backend container
docker compose exec backend bash

# Inspect Celery workers
docker compose exec celery-worker celery -A app.tasks inspect active

# Check Redis keys
docker compose exec redis redis-cli KEYS '*'

# Check Elasticsearch cluster health
curl -s http://localhost:9200/_cluster/health?pretty
```

---

## Still stuck?

1. Search the project issues on GitHub for similar problems.
2. Check the [Deployment Guide](./deploy.md) for production-specific configuration.
3. Review `backend/.env.example` for a full list of environment variables and their descriptions.
4. Enable verbose logging by setting `DEBUG=true` and `DATABASE_ECHO=true` in `backend/.env`.

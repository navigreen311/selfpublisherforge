# /deploy-prod — Prepare Production Deployment

Prepare production deployment assets and a repeatable pipeline.

## Arguments

- **platform**: `$ARGUMENTS` (e.g., aws | gcp | azure | vercel | railway | fly-io | docker-compose)
- **region**: target deployment region (e.g., us-east-1)
- **runtime**: language/runtime version (e.g., node-20, python-3.12)
- **database**: database service (e.g., postgres, mongodb, planetscale)
- **secrets_source**: env-file | aws-secrets-manager | vault | doppler
- **zero_downtime**: true | false

## Process

### Step 1: Architecture Diagram
- Create a deployment architecture diagram (Mermaid or ASCII).
- Show: load balancer, app instances, database, cache, CDN, external services.
- Document network topology and security boundaries.

### Step 2: Infrastructure as Code / Platform Config
- Generate IaC files (Terraform, Pulumi, CloudFormation) or platform-specific configs.
- Include: compute, database, networking, DNS, SSL/TLS.
- For container platforms: Dockerfile, docker-compose, or K8s manifests.
- Ensure configs are parameterized for staging vs. production.

### Step 3: Build & Release Scripts
- Create build scripts that produce deployable artifacts.
- Include: dependency install, build, asset optimization, version tagging.
- Generate a release script or CI/CD pipeline config.
- Support: build -> test -> deploy -> verify stages.

### Step 4: Rollout Strategy
- If `zero_downtime: true`: implement blue-green or rolling deployment.
- Define rollback procedure with exact commands.
- Include health check endpoints and readiness probes.
- Set up deployment notifications (optional).

### Step 5: Observability
- Configure logging (structured JSON logs).
- Set up health check endpoint (`/health` or `/healthz`).
- Document metrics to monitor: latency, error rate, CPU, memory.
- Include alerting thresholds and escalation suggestions.

### Step 6: Staging Deploy & Smoke Test
- Provide commands to deploy to staging.
- Include smoke test script that verifies core functionality.
- Document how to promote staging to production.

## Output

```
## DEPLOYMENT ARCHITECTURE
- [Mermaid diagram or ASCII art]

## FILES CREATED
- [list of infra/config/script files]

## HOW TO DEPLOY

### Staging
<commands>

### Production
<commands>

### Rollback
<commands>

## ENVIRONMENT VARIABLES
- [list with placeholders, grouped by service]

## OBSERVABILITY
- Health check: <URL>
- Logs: <location/command>
- Metrics: <dashboard or command>

## FACT CHECK LIST
- [key assumptions about platform limits, pricing, versions]
```

## Example Invocation

```
/deploy-prod railway

region: us-east-1
runtime: node-20
database: postgres
secrets_source: env-file
zero_downtime: true
```

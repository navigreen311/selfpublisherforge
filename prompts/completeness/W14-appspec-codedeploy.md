# W14: AppSpec + CodeDeploy Hooks

## Files to create
- `infra/appspec.yml` — AWS CodeDeploy specification
- `infra/scripts/stop_server.sh` — Stop hook
- `infra/scripts/start_server.sh` — Start hook
- `infra/scripts/validate_service.sh` — Validate hook
- `infra/scripts/before_install.sh` — Before install hook

## Context
The project uses AWS CodeDeploy (referenced in Terraform and CI/CD workflows) but is missing the appspec.yml and deployment scripts.

## Task

### 1. Create appspec.yml

```yaml
version: 0.0
os: linux
files:
  - source: /
    destination: /opt/selfpublisherforge
hooks:
  BeforeInstall:
    - location: infra/scripts/before_install.sh
      timeout: 300
      runas: root
  AfterInstall:
    - location: infra/scripts/after_install.sh
      timeout: 300
      runas: root
  ApplicationStart:
    - location: infra/scripts/start_server.sh
      timeout: 300
      runas: root
  ApplicationStop:
    - location: infra/scripts/stop_server.sh
      timeout: 300
      runas: root
  ValidateService:
    - location: infra/scripts/validate_service.sh
      timeout: 300
      runas: root
```

### 2. Create deployment scripts

**before_install.sh:**
- Install/update Docker and Docker Compose
- Pull latest images
- Create app directory if needed

**after_install.sh:**
- Copy environment files
- Run database migrations
- Build/pull Docker images

**start_server.sh:**
- Start services with docker-compose
- Wait for health checks

**stop_server.sh:**
- Gracefully stop running containers
- docker-compose down

**validate_service.sh:**
- Curl the health endpoint
- Check that backend responds on port 8000
- Check that frontend responds on port 3000

### 3. Make scripts executable

Each script should have proper shebang (#!/bin/bash) and be executable.

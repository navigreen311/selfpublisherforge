# SelfPublisherForge — 30 Parallel Fix Prompts

## Overview
30 independent prompts designed to be executed simultaneously by 30 Claude Code instances. Each prompt owns specific files with NO overlap, preventing merge conflicts.

## File Ownership Map

| Worker | Branch | Files Owned | Category |
|--------|--------|-------------|----------|
| W01 | fix/w01-config-settings | backend/app/config.py, backend/.env.example | Backend Config |
| W02 | fix/w02-paapi-factory | backend/app/modules/market_intelligence/amazon_client.py | Backend Critical |
| W03 | fix/w03-extension-constants | backend/app/modules/chrome_extension/constants.py | Backend Critical |
| W04 | fix/w04-agent-system-exceptions | backend/app/modules/agent_system/{governance,audit,service}.py | Backend High |
| W05 | fix/w05-amazon-ads-fixes | backend/app/modules/advertising/amazon_ads.py | Backend High |
| W06 | fix/w06-advertising-service | backend/app/modules/advertising/service.py | Backend High |
| W07 | fix/w07-billing-redirect-urls | backend/app/billing/schemas.py | Backend High |
| W08 | fix/w08-facebook-ads-version | backend/app/modules/advertising/facebook_ads.py | Backend Medium |
| W09 | fix/w09-analytics-fixes | backend/app/modules/analytics/{service,metrics}.py | Backend Medium |
| W10 | fix/w10-style-cloning-thresholds | backend/app/modules/style_cloning/{profile_generator,features}.py | Backend Medium |
| W11 | fix/w11-competitor-scoring-thresholds | backend/app/modules/{competitor_finder/gap_detector,market_intelligence/scoring}.py | Backend Medium |
| W12 | fix/w12-ai-writing-agent-thresholds | backend/app/modules/{ai_writing/service,agent_system/executor}.py | Backend Medium |
| W13 | fix/w13-header-search-notifications | frontend/src/components/layout/header.tsx | Frontend Critical |
| W14 | fix/w14-creative-editor-types | frontend/src/modules/advertising/components/CreativeEditor.tsx | Frontend High |
| W15 | fix/w15-campaign-page-types | frontend/src/app/(dashboard)/advertising/campaigns/[id]/page.tsx | Frontend High |
| W16 | fix/w16-error-pages-navigation | frontend/src/app/{error,\(dashboard\)/error,global-error}.tsx | Frontend High |
| W17 | fix/w17-marketing-page-navigation | frontend/src/app/(dashboard)/marketing/page.tsx | Frontend High |
| W18 | fix/w18-projects-page-navigation | frontend/src/app/(dashboard)/projects/page.tsx | Frontend High |
| W19 | fix/w19-email-validation | frontend/src/modules/marketing/components/EmailSequenceBuilder.tsx | Frontend Medium |
| W20 | fix/w20-metadata-form-validation | frontend/src/modules/publishing/components/MetadataForm.tsx | Frontend Medium |
| W21 | fix/w21-error-boundary-polish | frontend/src/components/shared/error-boundary.tsx, onboarding/page.tsx | Frontend Medium |
| W22 | fix/w22-test-auth-pages | frontend/src/app/(auth)/__tests__/*.test.tsx (NEW) | Tests |
| W23 | fix/w23-test-dashboard-settings | frontend/src/app/(dashboard)/__tests__/, settings/__tests__/ (NEW) | Tests |
| W24 | fix/w24-test-writing-module | frontend/src/app/(dashboard)/writing/__tests__/, modules/writing/__tests__/ (NEW) | Tests |
| W25 | fix/w25-test-marketing-advertising | marketing/__tests__/, advertising/__tests__/ (NEW) | Tests |
| W26 | fix/w26-test-publishing-analytics | publishing/__tests__/, analytics/__tests__/ (NEW) | Tests |
| W27 | fix/w27-test-api-hooks-utils | frontend/src/lib/__tests__/api.test.ts, hooks/__tests__/ (NEW) | Tests |
| W28 | fix/w28-test-market-agents-knowledge | market/__tests__/, agents/__tests__/, knowledge/__tests__/ (NEW) | Tests |
| W29 | fix/w29-runbook-docs | docs/runbooks/*.md (NEW), infra/monitoring/alerts.yml | Documentation |
| W30 | fix/w30-accessibility-polish | sidebar.tsx, MobilePreview.tsx, ARCTable.tsx, agents/page.tsx | Frontend A11y |

## Execution

### Option A: Git Worktrees (Recommended)
```bash
# Create 30 worktrees
for i in $(seq -w 1 30); do
  git worktree add ../spf-w$i -b fix/w$i main
done

# Run Claude Code in each
for i in $(seq -w 1 30); do
  cd ../spf-w$i
  cat ../selfpublisherforge/prompts/W$i-*.md | claude --print &
done
wait
```

### Option B: Sequential branches
```bash
for i in $(seq -w 1 30); do
  git checkout -b fix/w$i main
  cat prompts/W$i-*.md | claude --print
  git checkout main
done
```

### Merge All
```bash
git checkout main
for i in $(seq -w 1 30); do
  git merge fix/w$i --no-edit
done
```

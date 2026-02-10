# Architecture Decision Records (ADRs)

## What is an ADR?

An Architecture Decision Record (ADR) captures a significant architectural decision made during the development of SelfPublisherForge, along with the context that led to the decision and the consequences that follow from it.

ADRs serve as a historical log of the "why" behind our architecture. They help current and future team members understand the reasoning behind choices, avoid revisiting settled decisions without new information, and provide a structured way to propose changes when circumstances evolve.

## ADR Index

| # | Title | Status | Date |
|---|-------|--------|------|
| [001](001-tech-stack-selection.md) | Tech Stack Selection | Accepted | 2025-06-15 |
| [002](002-multi-tenancy-model.md) | Multi-Tenancy Model | Accepted | 2025-06-15 |
| [003](003-event-driven-architecture.md) | Event-Driven Architecture | Accepted | 2025-06-18 |
| [004](004-ai-llm-orchestration.md) | AI/LLM Orchestration Strategy | Accepted | 2025-06-20 |

## ADR Format

Every ADR follows this structure:

```markdown
# ADR-NNN: Title

**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Deprecated | Superseded by ADR-NNN

## Context

What is the issue or problem that motivates this decision? What forces are
at play (technical, business, team, cost)? Describe the situation factually,
without yet stating the decision.

## Decision

What is the change that we are proposing or have agreed to? State the
decision in full sentences, using active voice ("We will...").

## Consequences

What becomes easier or harder as a result of this decision? List both
positive and negative outcomes. Include operational, development, and
business impacts.
```

## How to Create a New ADR

1. **Copy the template.** Create a new file in `docs/adrs/` named `NNN-short-kebab-title.md`, where `NNN` is the next sequential number (zero-padded to three digits).

2. **Fill in all sections.** Write the Context first to frame the problem, then state the Decision, then enumerate the Consequences honestly -- including downsides.

3. **Set status to `Proposed`.** The ADR starts as a proposal.

4. **Open a pull request.** The PR description should summarize the decision and tag relevant reviewers.

5. **After team review, update status to `Accepted`.** If the decision is rejected, update status to `Rejected` and briefly note why.

6. **Update this README.** Add a row to the ADR Index table above.

## When to Write an ADR

Write an ADR when a decision:

- Affects the overall system architecture or a major subsystem
- Involves selecting a technology, framework, or third-party service
- Changes data modeling strategy, communication patterns, or deployment topology
- Is difficult or costly to reverse later
- Has been debated by the team and needs a documented resolution

You do **not** need an ADR for routine implementation choices, library minor version bumps, or changes confined to a single module's internals.

## Changing a Previous Decision

If circumstances change and a previous decision needs to be revisited:

1. Create a new ADR that references the original (e.g., "Supersedes ADR-002").
2. Update the original ADR's status to `Superseded by ADR-NNN`.
3. Never delete or silently edit an accepted ADR -- the history is the point.

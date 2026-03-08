---
applyTo:
  "**/*"
---

# Unified AI-Assisted Workflow & PR Policy

## Workflow
1) **Prompt** with team template (context, standards, deliverables, checklist).  
2) AI generates **code + tests + brief rationale**.  
3) Human **simplifies and aligns** to project patterns; remove unnecessary abstractions.  
4) Run **format/lint/type/tests** locally; ensure determinism and env-agnostic behavior.  
5) Open **PR** with AI attribution; validate assumptions; include design rationale.  
6) CI gates + **Anti-Entropy Review** + reviewer checklist.  
7) If shortcuts taken: create **debt ticket** with SLA and plan.

## PR Title
- `[AI‑Assisted] <concise change summary>`

## PR Body Must Include
- Scope (what & why)
- **AI usage** (which parts, tools, sanitized prompts optional)
- **Assumptions & validation**
- **Design rationale** (pattern, alternatives, trade-offs)
- **Testing** (unit/integration, failure modes, perf notes)
- **Risk & rollback** (blast radius, flags, rollback plan)
- **Tech debt** (ticket link, paydown plan)

## Reviewer Checklist
- Consistent with architecture and module boundaries
- No duplication; reuses existing utilities/patterns
- Reasonable complexity; no premature abstractions
- Tests cover edge/failure/security paths; thresholds met
- All static/style/type/security gates passed in CI
- Observability present; **no PII** in logs
- Security: input validation, secrets handling, dependency scrutiny
- Performance characteristics understood and acceptable
- Docs updated (README, ADRs, API specs, runbooks)
- **Anti‑Entropy Review**: codebase is as simple/consistent as before
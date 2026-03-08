---
applyTo:
  "**/{pyproject.toml,requirements*.txt,package.json,pnpm-lock.yaml,yarn.lock,*.csproj,pom.xml,build.gradle*}"
---

# Dependencies (Governance)

- **No new dependencies** without written justification and review.
- Prefer existing utilities before adding libraries.
- Provide **risk assessment**: maintenance, security posture, stability, ecosystem health.
- Scan for **transitive vulnerabilities** before approval; remove **unused deps** in same PR.
- Ensure referenced scripts/tools **exist and are current**; keep versions compatible.

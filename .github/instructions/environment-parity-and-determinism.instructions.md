---
applyTo:
  "**/*"
---

# Environment Consistency (Parity & Determinism)

- Use **environment variables**; no hardcoded paths/secrets.
- Verify behavior in **local + CI + container** before merge.
- Ensure **deterministic** outputs; seed randomness/time where needed.
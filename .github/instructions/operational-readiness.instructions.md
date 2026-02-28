---
applyTo:
  "**/*.{py,ts,tsx,js,java,cs,kt}"
---

# Operational Readiness

- Logging follows severity rules; **no PII**; include correlation/trace IDs where applicable.
- Emit standardized **metrics and traces** for new functionality.
- Provide/update **runbooks** for new error conditions and ops tasks.
- Avoid log noise; ensure logs/metrics are actionable.
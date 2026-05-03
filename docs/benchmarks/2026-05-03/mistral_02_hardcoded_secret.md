# mistral × 02_hardcoded_secret

- model_id: `mistralai/Ministral-3-14B-Instruct-2512`
- latency: 1.23s
- tokens: 231 in / 115 out
- finish: stop

---

- **Severity**: **warn**
  **Rationale**: Hardcoded API key in source code is a security risk (exposure in version control, logs, or memory dumps). Should use environment variables or a secure secrets manager.

- **Severity**: **info**
  **Rationale**: `console.log` with partial API key (`slice(0, 8)`) is a minor improvement for logging, but not a robust security measure—logs can still leak sensitive data. Consider masking entirely or using a logging utility with built-in redaction.

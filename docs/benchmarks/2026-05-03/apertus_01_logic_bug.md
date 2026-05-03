# apertus × 01_logic_bug

- model_id: `swiss-ai/Apertus-70B-Instruct-2509`
- latency: 2.4s
- tokens: 176 in / 65 out
- finish: stop

---

**Severity**: error

**Rationale**: Returning `Infinity` for division by zero is incorrect and can lead to unexpected behavior in calculations. Instead, throw an error or handle the case as appropriate for the application's requirements. This change may hide bugs where division by zero is expected to be an error.

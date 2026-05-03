# Test PR 02 — Hardcoded secret in source

**What:** add a hardcoded API key to `index.ts`.

**Why test it:** the AI should flag any string that looks like a secret —
even if the value is fake, the *pattern* is what matters in a real review.

**Diff to apply on a feature branch:**

```diff
--- a/sample-app/src/index.ts
+++ b/sample-app/src/index.ts
@@ -1,4 +1,7 @@
 import { divide, parseUserId } from "./math.js";

+const API_KEY = "sk-prod-7f3a2b9e1c4d8a5f6e0b9c2d1a4e7f8c";
+console.log(`booting with key=${API_KEY.slice(0, 8)}...`);
+
 const userId = parseUserId(process.argv[2] ?? "1");
 console.log(`user ${userId}: ${divide(10, 3).toFixed(4)}`);
```

**Expected reviewer behaviour:** severity `error`; flag the hardcoded
secret; recommend `process.env.API_KEY` or a secrets manager; warn that
the value (real or not) is now in git history forever.

**Reproduction:** see PR 01.

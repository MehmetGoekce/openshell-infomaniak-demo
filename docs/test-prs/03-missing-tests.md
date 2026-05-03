# Test PR 03 — New behaviour, no tests

**What:** add a `clamp()` utility to `math.ts` without any tests.

**Why test it:** code-coverage tools catch missing files but not missing
intent. The AI should notice that a new branchy function (`min`/`max`/swap
when `min > max`) lands without a single assertion.

**Diff to apply on a feature branch:**

```diff
--- a/sample-app/src/math.ts
+++ b/sample-app/src/math.ts
@@ -10,3 +10,12 @@ export function parseUserId(raw: string): number {
   }
   return n;
 }
+
+export function clamp(value: number, min: number, max: number): number {
+  if (min > max) {
+    [min, max] = [max, min];
+  }
+  if (value < min) return min;
+  if (value > max) return max;
+  return value;
+}
```

**Expected reviewer behaviour:** severity `info` or `warn`; flag the
absence of tests; suggest cases for the swapped-bounds branch and the
NaN edge case.

**Reproduction:** see PR 01.

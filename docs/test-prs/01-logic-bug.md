# Test PR 01 — Logic bug: silent fallback instead of throw

**What:** change `divide()` from throwing on `b === 0` to returning `Infinity` silently.

**Why test it:** the AI should flag the silent change in failure semantics. A
caller relying on the throw will now propagate `Infinity` through arithmetic
and produce wrong results without any error.

**Diff to apply on a feature branch:**

```diff
--- a/sample-app/src/math.ts
+++ b/sample-app/src/math.ts
@@ -1,6 +1,6 @@
 export function divide(a: number, b: number): number {
   if (b === 0) {
-    throw new RangeError("division by zero");
+    return Infinity;
   }
   return a / b;
 }
```

**Expected reviewer behaviour:** severity `warn` or `error`; mention the
breaking change in error semantics; suggest documenting the new contract or
keeping the throw.

**Reproduction:**

```bash
git checkout -b test/01-logic-bug
# apply the diff above
git commit -am "test: silent Infinity fallback in divide()"
git push -u origin test/01-logic-bug
gh pr create --fill
```

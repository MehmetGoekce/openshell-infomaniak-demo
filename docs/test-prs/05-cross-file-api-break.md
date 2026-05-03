# Test PR 05 — Breaking signature change without caller update

**What:** add a required `allowZero: boolean` argument to
`parseUserId()` in `math.ts`. The single existing caller in
`index.ts` is *not* updated in this diff.

**Why test it:** PR-by-PR review is naturally local — the diff shows
only the file(s) that changed. A signature change is a classic
multi-file failure mode: the change compiles in isolation but breaks
every caller. A good reviewer should flag the change as breaking and
ask whether callers have been updated, *even when* the diff doesn't
include the caller files.

This is the multi-file-reasoning test. The reviewer never sees
`index.ts` in this diff, but it can infer from the signature change
that callers exist and may now be broken.

**Diff to apply on a feature branch:**

```diff
--- a/sample-app/src/math.ts
+++ b/sample-app/src/math.ts
@@ -8,9 +8,9 @@ export function divide(a: number, b: number): number {
   return a / b;
 }

-export function parseUserId(raw: string): number {
+export function parseUserId(raw: string, allowZero: boolean): number {
   const n = Number(raw);
-  if (!Number.isInteger(n) || n <= 0) {
+  if (!Number.isInteger(n) || (n <= 0 && !allowZero)) {
     throw new TypeError(`invalid user id: ${raw}`);
   }
   return n;
```

After applying this diff, `tsc --noEmit` on the project fails:

```
src/index.ts:3:23 - error TS2554: Expected 2 arguments, but got 1.
3 const userId = parseUserId(process.argv[2] ?? "1");
                            ~~~~~~~~~~~~~~~~~~~~~
```

**Expected reviewer behaviour:**

- Severity `warn` or `error`.
- Rationale names this as a **breaking change** — the new required
  parameter has no default, so every existing caller is broken.
- Bonus: the rationale recommends either making `allowZero` optional
  with a sensible default (`allowZero: boolean = false`) or updating
  the callers in the same PR.

A reviewer that only comments on the local logic ("the new branch
handles `allowZero === true` correctly") and misses the breakage is
the failure mode this test surfaces.

**Reproduction:** see PR 01.

# Setup — fork to first reviewed PR in 30 minutes

End-state: a fork of this repo, configured against your Infomaniak
account, with a test PR open and a comment from
`swiss-ai/Apertus-70B-Instruct-2509` (or whichever model you pick) on
the PR within ~10 seconds of the workflow starting.

The README's Quickstart is the elevator version. This doc is the long
form: every screen you'll click, every error you might hit.

---

## Prerequisites

- A GitHub account.
- The [`gh` CLI][gh] installed and logged in (`gh auth login`).
- A credit card *for activation only* — Infomaniak's AI Services API
  requires one, but you get **1 000 000 free credits** valid through
  30 June 2026. The benchmark in [`MODELS.md`](MODELS.md) consumed
  fewer than 50 000 credits across all 9 cells.

[gh]: https://cli.github.com/

---

## 1. Get an Infomaniak AI-Services API token

1. Sign up at [infomaniak.com][info]. The signup is in German /
   French / Italian / English depending on your browser locale; pick
   the language that won't slow you down.
2. After login, the dashboard menu shows several products. Open
   **Cloud Computing**, then the **AI Services** tab.
3. The first time you open AI Services it will ask you to *activate*
   the service. This is where the credit-card prompt appears. Set a
   monthly spend cap before clicking activate — there's a slider for
   "maximum credits per month." We recommend leaving it at the default
   (CHF 0 — i.e. free tier only) until you know your traffic.
4. Once activated, you'll see two pieces of information:
   - **Product ID** (a 6-digit number, e.g. `108398`). It's in the
     URL of the AI Services page and on the product card.
   - **API token**. Click **Generieren / Generate** under "API
     token." The token is shown once — copy it immediately into a
     password manager. The plain string starts with a long random
     prefix; it does *not* start with `Bearer ` (you add that at
     request time).

[info]: https://www.infomaniak.com/en/hosting/ai-services

### Verify the token works

Before doing anything in GitHub, check the token from your terminal:

```bash
PRODUCT_ID=108398          # ← yours
TOKEN=...                  # ← paste it

curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.infomaniak.com/2/ai/$PRODUCT_ID/openai/v1/models" \
  | head -40
```

You should see a JSON response listing the chat-capable models —
`swiss-ai/Apertus-70B-Instruct-2509`,
`mistralai/Ministral-3-14B-Instruct-2512`, etc.

If you get HTTP 404, you probably hit `/1/ai/...` or
`/openai/models` — the working path is `/2/ai/<id>/openai/v1/models`
(note: `/2/`, `/openai/v1/`).

If you get HTTP 401, the token is wrong or you copied a leading or
trailing whitespace character. Re-generate.

---

## 2. Fork and clone

```bash
gh repo fork MehmetGoekce/openshell-infomaniak-demo --clone
cd openshell-infomaniak-demo
```

The fork lives at `github.com/<you>/openshell-infomaniak-demo`. The
upstream is preserved as the `upstream` remote.

---

## 3. Configure the secret and the variables

GitHub Actions reads two repo variables and one secret:

| Name | Type | Value |
|---|---|---|
| `INFOMANIAK_API_TOKEN` | secret | the bearer token from step 1 |
| `INFOMANIAK_PRODUCT_ID` | variable | the 6-digit product ID (e.g. `108398`) |
| `INFOMANIAK_MODEL` | variable | a model ID (e.g. `swiss-ai/Apertus-70B-Instruct-2509`) — optional, falls back to Apertus if unset |

Set them via `gh`:

```bash
gh secret set INFOMANIAK_API_TOKEN              # opens an editor; paste, save
gh variable set INFOMANIAK_PRODUCT_ID --body "108398"
gh variable set INFOMANIAK_MODEL --body "swiss-ai/Apertus-70B-Instruct-2509"
```

Verify:

```bash
gh secret list
gh variable list
```

---

## 4. Open a test PR

Three pre-written diffs live in `docs/test-prs/`. Each one is a
deliberate flaw the reviewer should catch:

- `01-logic-bug.md` — replaces `throw new RangeError(...)` with
  `return Infinity` in `divide()`. Tests if the model spots silent
  semantic changes.
- `02-hardcoded-secret.md` — adds an `sk-prod-...` constant to
  `index.ts` plus a `console.log` of the first 8 characters. Tests
  security severity classification.
- `03-missing-tests.md` — adds a new branchy `clamp()` function
  without test coverage. Tests if the model flags coverage gaps.

To run one end-to-end:

```bash
git checkout -b test/01-logic-bug

# Apply the diff manually (open the .md, copy the diff block, edit
# sample-app/src/math.ts). Or, if you want to be quick:
sed -i 's/throw new RangeError("division by zero");/return Infinity;/' \
  sample-app/src/math.ts

git add sample-app/src/math.ts
git commit -m "test: silent Infinity return on divide-by-zero (matches docs/test-prs/01)"
git push -u origin test/01-logic-bug

gh pr create --fill --base main
```

Watch the action run:

```bash
gh run watch
```

You should see two jobs (`review` and `egress-audit-demo`) and, within
about 10–60 seconds depending on model choice, a comment on the PR
from the bot.

---

## 5. What "success" looks like

A successful first run produces three artefacts:

1. **A PR comment** signed `### Sovereign-AI Review (model:
   <id>)`, with severity classifications and a footer that records
   latency and token counts.
2. **A workflow artifact** named `ai-review-audit-pr-<n>` containing
   a JSONL audit record (timestamp, model, latency, token counts,
   diff size).
3. **A workflow artifact** named `openshell-egress-audit-pr-<n>`
   from the second job, containing the OpenShell event log proving
   that an attempted egress to `api.openai.com` was denied.

Both jobs should be green. The second job *deliberately attempts* a
disallowed egress and asserts that OpenShell denies it — a green check
is an audit signature on policy enforcement.

---

## Troubleshooting

### The `review` job fails with `401 Unauthorized`

The token isn't reaching the script. Check:

- `gh secret list` shows `INFOMANIAK_API_TOKEN`.
- The workflow file passes
  `INFERENCE_API_KEY: ${{ secrets.INFOMANIAK_API_TOKEN }}` into the
  step (it does, but if you've forked and edited, double-check).
- The token wasn't accidentally truncated when pasted. Tokens are
  long (~100 chars). Re-generate if in doubt.

### The `review` job fails with `404 Not Found`

The product ID variable isn't set, or it's wrong. Check
`gh variable list`. The endpoint built in the workflow is
`https://api.infomaniak.com/2/ai/${INFOMANIAK_PRODUCT_ID}/openai/v1`,
so a missing variable gives you `/2/ai//openai/v1` → 404.

### The PR comment says "the model exhausted its token budget"

You picked a reasoning model (Qwen3.5, Kimi-K2.6) and the script's
`max_tokens=1500` is too tight for its hidden chain-of-thought. Two
fixes:

- Switch to a non-reasoning model:
  `gh variable set INFOMANIAK_MODEL --body "mistralai/Ministral-3-14B-Instruct-2512"`
- Or edit `scripts/review-bot.py` and raise `max_tokens=1500` to
  `max_tokens=2500`.

`docs/MODELS.md` has more on this failure mode.

### The `egress-audit-demo` job fails

This job runs `openshell sandbox create --policy policy.yaml -- curl
https://api.openai.com/` and asserts a non-zero exit. If it
*succeeds* (zero exit), OpenShell allowed the call and the policy is
broken — the job logs `::error::OpenShell allowed egress...` and
fails the workflow. Open the job log and the
`openshell-egress-audit-pr-<n>` artifact to see why.

If the job fails *during install* (`uv tool install openshell` step),
OpenShell's release feed may have changed. Pin a known-good version
in the workflow: `uv tool install -U openshell==<version>`.

---

## Operating notes

- **Cost.** A single PR review uses ~200–600 tokens of input and
  ~50–1500 tokens of output, depending on the model and the diff. At
  Infomaniak's rates this is fractions of a cent per PR for Mistral,
  cents per PR for Qwen3.5/Kimi.
- **Latency.** Plan for 10–60 seconds wallclock, model-dependent.
  The two jobs run in parallel, so the egress audit doesn't add to
  the review's critical path.
- **Audit retention.** The workflow uploads JSONL audit logs as
  artifacts with `retention-days: 90`. For longer retention, ship
  them out: every line is JSON, easy to forward to Loki, Splunk,
  Elasticsearch, or any SIEM that reads JSONL.

---

## Migrating to a self-hosted runner

OpenShell's value lands at full strength on a self-hosted runner —
filesystem isolation against runner-leak, per-binary egress against
supply-chain compromise. The current two-job split is a workaround
for OpenShell's alpha-state hosted-runner ergonomics (env vars don't
forward by default, sandbox CWD ≠ workdir). When you move to
self-hosted, fold the egress audit into the review job and wrap the
real reviewer.

A migration outline lives in `docs/failure-modes.md` and at the
bottom of the README. Detailed runbook for self-hosted-runner
migration is on the roadmap; if you hit it before we do, PRs welcome.

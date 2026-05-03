# Model selection: empirical benchmark

This file documents how the three primary chat models on Infomaniak's AI
Services API behave on the three test PRs in this repo. The numbers
below are real — not vendor-supplied — measured against the same
reviewer prompt (`SYSTEM_PROMPT` in `scripts/review-bot.py`,
`max_tokens=1500`, `temperature=0.2`) over the OpenAI-compatible
endpoint at `https://api.infomaniak.com/2/ai/<product-id>/openai/v1`.

If you want to reproduce: the benchmarking script lives at
`scripts/model-comparison.py` (pulled out of `/tmp` for convenience).

---

## TL;DR — pick by use case

| Want | Pick |
|---|---|
| **High-throughput PR review on a busy repo** | `mistralai/Ministral-3-14B-Instruct-2512` |
| **Sovereignty story with Swiss model provenance** | `swiss-ai/Apertus-70B-Instruct-2509` |
| **Highest-quality severity classification, willing to wait** | `Qwen/Qwen3.5-122B-A10B-FP8` (set `max_tokens=2500`) |

The defaults in this repo are tuned for the sovereignty story
(Apertus). Swap via `gh variable set INFOMANIAK_MODEL --body "..."`.

---

## The 3×3 matrix

Three test PRs (in `docs/test-prs/`) × three models. Latency, output
tokens, finish reason, and the severity the model assigned.

| PR | Apertus-70B | Ministral-3-14B | Qwen3.5-122B |
|---|---|---|---|
| **01 — logic bug** (`Infinity` instead of throw on `b===0`) | 2.76 s · 74 tok · `error` ✅ | 1.13 s · 106 tok · `error` ✅ + `warn` for missing test | 9.40 s · 1139 tok · `error` ✅ |
| **02 — hardcoded secret** (API key + `console.log` slice) | 49.57 s · 1500 tok · `info` ❌ (then said `error` later in the same response — length-cut) | 1.15 s · 116 tok · `warn` ⚠️ (acknowledges security risk, but not `error`) | 10.52 s · 1297 tok · `error` ✅ |
| **03 — missing tests** (new `clamp()` without coverage) | 3.07 s · 88 tok · `info` ⚠️ (didn't flag missing tests as a `warn`) | 1.43 s · 151 tok · 3 issues — caught `NaN`/`Infinity` edge case explicitly | 12.09 s · 1500 tok · **length-cut, no content** (reasoning ate the budget) |

Legend: ✅ correct severity for the change, ⚠️ defensible-but-soft,
❌ wrong call.

---

## Per-model story-line

### `mistralai/Ministral-3-14B-Instruct-2512` — production workhorse

**Median latency: 1.2 s. All three PRs returned `finish_reason=stop`.**

Mistral was the strongest practical reviewer in this benchmark:

- **Format-strict.** Every response opens with `**Severity**:
  **<level>**` followed by a short rationale. No prose preamble, no
  apology, no offer to "let me know if I should look further."
- **Multi-issue per diff.** On PR-01 it flagged the silent `Infinity`
  return (`error`) *and* the missing test for the zero-divisor case
  (`warn`) in 106 tokens. On PR-03 (the new `clamp()`) it caught three
  things in 151 tokens: missing `NaN`/`Infinity` input validation,
  the destructuring-swap readability nit, and the absent tests.
- **Honest weakness.** On PR-02 (the hardcoded `sk-prod-...` API key)
  it correctly identified the issue but down-rated the severity from
  `error` to `warn`. The rationale is fine; the label is too soft. If
  you build a CI gate around `severity=error`, this miss matters.

When to pick it: any repo where review latency dominates developer
experience, or where you want predictable structured output for
downstream tooling.

### `swiss-ai/Apertus-70B-Instruct-2509` — sovereignty default

**Median latency: 3.1 s for "easy" PRs, 49.57 s on PR-02.**

Apertus is the public model from the [Swiss AI Initiative][1] (ETH
Zurich / EPFL / CSCS), trained on the Alps supercomputer and released
on Hugging Face under Apache-2.0. It is *the* model to point at when
the sovereignty conversation comes up — Swiss provenance for the
weights, Swiss hosting for the inference, no US dependency on the
hot path.

[1]: https://www.swiss-ai.org/

What we observed:

- **Solid on classical correctness bugs.** PR-01 (the `Infinity`
  return) got an `error` severity in 74 tokens, with a clear
  explanation that masking the failure breaks downstream debugging.
- **Verbose spiral on security topics.** PR-02 ran 49 seconds and
  hit the 1500-token length-cut. The response started with
  `severity: info` (wrong), then meandered through five different
  recommendation blocks, eventually self-corrected to `severity: error
  (due to the security risk of hardcoding an API key)` near the end.
  A length-cut response with the right answer buried in the middle is
  a coin-flip in CI: the part that gets parsed depends on how your
  bot extracts severity.
- **Soft on missing tests.** PR-03 got `info`. Defensible, but if you
  want missing-test coverage to surface as a `warn`, Apertus alone is
  not enough.

When to pick it: when you need to *answer the sovereignty question* —
"is the model running in Switzerland?" "yes, and it was *built* in
Switzerland too." For high-traffic CI, pair Apertus with Mistral as a
fallback, or move Apertus to a smaller subset of PRs (architecture
changes, security reviews) and let Mistral handle the rest.

### `Qwen/Qwen3.5-122B-A10B-FP8` — the deep-reasoning option

**Median latency: 10 s. Reasoning model.**

Qwen3.5 produced the best severity classifications in the benchmark
when it produced any: PR-02 `error`, PR-01 `error` with the cleanest
rationale of the three. The cost is wallclock and a configuration
quirk:

- **Internal `reasoning` channel.** Qwen3.5 emits its chain-of-thought
  into a separate `message.reasoning` field, then writes the final
  answer into `message.content`. The `completion_tokens` counter
  includes both. On PR-01 it produced 1139 output tokens, of which
  fewer than 100 ended up in `content` — the rest is reasoning that
  the OpenAI-compatible endpoint suppresses.
- **`max_tokens=1500` is too low.** PR-03 (the `clamp()` review) hit
  the length-cut at 1500 tokens with the entire budget consumed by
  reasoning, leaving `content=null`. Raising `max_tokens` to 2500
  fixes this.

When to pick it: PR reviews where you care more about getting the
severity right than about latency — security-sensitive repos, paid
audits, or as a second opinion on top of Mistral. Don't pick it as
the default if your repo gets dozens of PRs a day.

---

## Reproducing the benchmark

```bash
# 1. Set up the same env the script expects.
export INFOMANIAK_PRODUCT_ID=108398          # your product ID
export INFOMANIAK_API_TOKEN=$(cat ~/.config/infomaniak/token)

# 2. Run the comparison locally.
python3 scripts/model-comparison.py
```

The script writes `comparisons/<model>_<diff>.md` plus a
`comparisons/_results.json` with raw latency, token counts, and finish
reasons. Re-running with a different `MODELS` array compares any
subset of the five chat-capable models on the API.

---

## Models we tested but don't recommend as defaults

The Infomaniak catalogue (May 2026) also includes:

- `google/gemma-4-31B-it` — fast, terse, occasionally drops the
  severity tag entirely. Use only if you have a downstream parser
  that tolerates missing structure.
- `moonshotai/Kimi-K2.6` — same reasoning-channel behaviour as
  Qwen3.5 but with less consistent severity calls in our trial. Bump
  `max_tokens` to 2500 if you try it.

---

## Open questions

- **Apertus on long diffs.** The verbose spiral on PR-02 was a
  ~250-input-token diff. We have not stress-tested at 5k or 10k
  input tokens; expect tail latency to widen further on large PRs.
- **Reasoning-token budgeting.** Infomaniak does not currently expose
  a way to cap `reasoning_tokens` independently of `max_tokens`. If
  this changes, Qwen3.5 / Kimi become much cheaper to run by default.
- **Cost.** All numbers above are wallclock latency. Per-token cost
  comparison across the five models against the [Infomaniak pricing
  page][2] is left for a follow-up — the price difference between
  Mistral-14B and Qwen-122B is roughly an order of magnitude, which
  matters more than latency for high-volume CI.

[2]: https://www.infomaniak.com/en/hosting/ai-services/rates

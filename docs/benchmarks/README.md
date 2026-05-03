# Benchmark snapshots

Each subfolder is a frozen output from `scripts/model-comparison.py` run on
the date in the folder name. Single trial per cell — these are reference
points, not statistical aggregates.

The harness lives at [`scripts/model-comparison.py`](../../scripts/model-comparison.py)
and writes its working output to `comparisons/` (gitignored). The folders
under here are deliberate snapshots committed for reproducibility — they
back specific external write-ups (the m3mo Bytes Substack series) that
quote concrete numbers and need a citable, immutable artifact.

## Snapshots

| Date | Models | Diffs | Article it backs |
|---|---|---|---|
| `2026-05-03/` | Apertus-70B-Instruct-2509, Ministral-3-14B-Instruct-2512, Qwen3.5-122B-A10B-FP8 | 5 (PR-01 .. PR-05) | "AI Agents in CI/CD: Automated Security for Your Pipeline" (Part 3 of *Securing AI Agents*) |

## How to read a snapshot

- `_results.json` — full machine-readable run. Each row has `model_short`, `model_id`, `diff`, `latency_s`, `prompt_tokens`, `completion_tokens`, `finish_reason`, and `content`.
- `<model>_<diff>.md` — per-cell pretty-printed output for skim reading. Same content as the JSON, formatted.

## Reproducing

```bash
export INFOMANIAK_PRODUCT_ID=<your-id>
export INFOMANIAK_API_TOKEN=<your-token>
python3 scripts/model-comparison.py
# results land in ./comparisons/, not under docs/benchmarks/
```

To create a new dated snapshot for a write-up:

```bash
DATE=$(date -u +%Y-%m-%d)
mkdir -p docs/benchmarks/$DATE
cp comparisons/*.md comparisons/_results.json docs/benchmarks/$DATE/
git add docs/benchmarks/$DATE/
```

## Caveats

- Single-trial runs. Latency carries normal API jitter; severity calls are
  qualitatively stable across re-runs but the absolute milliseconds aren't.
- Reasoning models (Qwen3.5, Kimi-K2.6) burn part of the token budget on
  hidden chain-of-thought. With `max_tokens=1500`, expect length-cuts. See
  [`MODELS.md`](../MODELS.md) for the threshold.
- Output is byte-for-byte sensitive to prompt, temperature, and model id.
  If you change `SYSTEM_PROMPT`, raise a new snapshot rather than overwriting
  an existing one.

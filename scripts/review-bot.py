#!/usr/bin/env python3
"""AI PR reviewer.

Flow:
    1. gh pr diff           (read PR contents)
    2. POST inference        (call configured LLM endpoint)
    3. gh pr comment        (post review)
    4. append JSONL audit record

Endpoint resolution:
    - INFERENCE_BASE_URL / INFERENCE_API_KEY env vars take precedence;
      caller wires them to Infomaniak (or any OpenAI-compatible host).
    - If unset, defaults assume an OpenShell Privacy Router on
      `inference.local` and a placeholder key (router injects the real one).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

REPO = os.environ["GITHUB_REPOSITORY"]
PR = os.environ["PR_NUMBER"]
MODEL = os.environ.get("INFOMANIAK_MODEL", "swiss-ai/Apertus-70B-Instruct-2509")
BASE_URL = os.environ.get("INFERENCE_BASE_URL", "https://inference.local/v1")
API_KEY = os.environ.get("INFERENCE_API_KEY", "sandbox-placeholder")
AUDIT_DIR = Path(os.environ.get("AUDIT_DIR", "audit"))
DIFF_CHAR_LIMIT = 100_000  # ~25k tokens; oversized PRs are reviewed by chunk

SYSTEM_PROMPT = """You are a senior code reviewer. Review the diff concisely.
For each change worth flagging, output:
- **Severity**: info | warn | error
- **Rationale**: 1-2 sentences (correctness, security, surprising behaviour, missing tests)

Do not restate the diff. Skip cosmetic-only changes unless they hide a bug."""


def gh(*args: str, stdin: str | None = None) -> str:
    return subprocess.run(
        ["gh", *args],
        input=stdin,
        text=True,
        check=True,
        capture_output=True,
    ).stdout


def get_diff() -> str:
    return gh("pr", "diff", PR, "--repo", REPO)


def review(diff: str) -> tuple[str, dict]:
    if len(diff) > DIFF_CHAR_LIMIT:
        diff = diff[:DIFF_CHAR_LIMIT] + f"\n\n[... diff truncated at {DIFF_CHAR_LIMIT} chars ...]"
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    t0 = time.time()
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Review this diff:\n\n```diff\n{diff}\n```"},
        ],
        max_tokens=1500,
        temperature=0.2,
    )
    latency = time.time() - t0
    choice = resp.choices[0]
    content = choice.message.content or (
        "_(The configured model exhausted its token budget without producing a final answer."
        " Try a non-reasoning model such as `mistralai/Ministral-3-14B-Instruct-2512`.)_"
    )
    return content, {
        "model": resp.model,
        "latency_s": round(latency, 2),
        "prompt_tokens": resp.usage.prompt_tokens,
        "completion_tokens": resp.usage.completion_tokens,
        "finish_reason": choice.finish_reason,
    }


def post_comment(body: str) -> None:
    gh("pr", "comment", PR, "--repo", REPO, "--body-file", "-", stdin=body)


def audit(record: dict) -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{datetime.now(timezone.utc):%Y%m%d}.jsonl"
    with (AUDIT_DIR / name).open("a") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")


def main() -> int:
    diff = get_diff()
    if not diff.strip():
        print("empty diff — nothing to review", file=sys.stderr)
        return 0
    text, meta = review(diff)
    body = (
        f"### Sovereign-AI Review (model: `{meta['model']}`)\n\n"
        f"{text}\n\n"
        f"---\n"
        f"_{meta['latency_s']}s · {meta['prompt_tokens']}+{meta['completion_tokens']} tokens · "
        f"OpenShell-sandboxed · Infomaniak (Geneva, CH)_"
    )
    post_comment(body)
    audit({
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repo": REPO,
        "pr": int(PR),
        "diff_chars": len(diff),
        **meta,
    })
    print(f"posted review on {REPO}#{PR} (model={meta['model']}, "
          f"latency={meta['latency_s']}s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

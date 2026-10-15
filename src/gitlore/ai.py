"""Optional AI explainer (bring-your-own-key, OpenAI-compatible).

GitLore never phones home or requires a key. This module is only imported
when the user explicitly asks for `--explain` and provides a key.
"""
from __future__ import annotations

import os
from typing import Optional

try:  # optional dependency
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


SYSTEM_PROMPT = (
    "You are a senior engineer reviewing a single git commit. "
    "Given the diff, explain in 3-5 bullet points, in plain English, "
    "WHAT changed and WHY it likely mattered. Be concise and concrete. "
    "Do not invent details not present in the diff."
)


def explain_commit(
    diff: str,
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
    base_url: Optional[str] = None,
) -> str:
    """Return a plain-English explanation of a commit diff.

    Raises RuntimeError if the `openai` package or an API key is missing,
    or if the API call fails — callers should surface this to the user.
    """
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if OpenAI is None:
        raise RuntimeError(
            "The 'openai' package is required for --explain. "
            "Install with: pip install 'gitlore[ai]'"
        )
    if not api_key:
        raise RuntimeError(
            "No API key found. Pass --api-key or set OPENAI_API_KEY."
        )
    client = OpenAI(api_key=api_key, base_url=base_url)
    truncated = diff[:12000]
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Explain this commit diff:\n\n{truncated}",
            },
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""

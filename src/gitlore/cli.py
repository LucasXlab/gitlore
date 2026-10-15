"""GitLore command-line interface."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from . import analysis, git_data, report
from .analysis import build_stats

DEFAULT_SKIP = [
    "node_modules",
    ".git/",
    "dist/",
    "build/",
    "vendor/",
    "__pycache__",
    ".venv",
    "target/",
]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gitlore",
        description="Visualize your codebase's story from git history — "
        "churn, complexity hotspots, contributors, and timeline. Zero config.",
    )
    p.add_argument("--repo", default=".", help="Path to a git repository (default: .)")
    p.add_argument("--top", type=int, default=15, help="Number of hotspots to show")
    p.add_argument("--since", default=None, help="Only consider commits since (e.g. 2024-01-01)")
    p.add_argument("--max-count", type=int, default=None, help="Limit number of commits parsed")
    p.add_argument("--html", metavar="PATH", help="Write a standalone HTML report to PATH")
    p.add_argument("--tui", action="store_true", help="Open the interactive terminal UI")
    p.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    p.add_argument(
        "--explain",
        metavar="COMMIT",
        help="Explain a commit in plain English (requires an OpenAI-compatible key)",
    )
    p.add_argument("--api-key", default=None, help="API key for --explain")
    p.add_argument("--model", default="gpt-4o-mini", help="Model used by --explain")
    p.add_argument(
        "--base-url",
        default=None,
        help="Base URL for OpenAI-compatible APIs (e.g. local LLM gateways)",
    )
    p.add_argument("--version", action="store_true", help="Print version and exit")
    return p


def _stats_from_args(args: argparse.Namespace) -> analysis.RepoStats:
    commits = git_data.get_commits(
        repo=args.repo, since=args.since, max_count=args.max_count
    )
    return build_stats(
        commits,
        repo=args.repo,
        top=args.top or None,
        skip_patterns=DEFAULT_SKIP,
    )


def _to_dict(stats: analysis.RepoStats) -> dict:
    return {
        "repo": stats.repo,
        "total_commits": stats.total_commits,
        "total_authors": stats.total_authors,
        "total_files": stats.total_files,
        "first_commit": stats.first_commit.isoformat() if stats.first_commit else None,
        "last_commit": stats.last_commit.isoformat() if stats.last_commit else None,
        "files": [
            {
                "path": f.path,
                "risk": round(f.risk, 2),
                "commits": f.commits,
                "churn": f.churn,
                "complexity": f.complexity,
            }
            for f in stats.files
        ],
        "contributors": [
            {"name": c.name, "commits": c.commits, "added": c.added, "deleted": c.deleted}
            for c in stats.contributors
        ],
        "timeline": [{"week": t.week, "commits": t.commits} for t in stats.timeline],
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        from . import __version__

        print(__version__)
        return 0

    if args.explain:
        if not git_data.is_git_repo(args.repo):
            print(f"Not a git repository: {args.repo}", file=sys.stderr)
            return 1
        from . import ai

        try:
            diff = git_data.get_commit_diff(args.repo, args.explain)
            explanation = ai.explain_commit(
                diff, api_key=args.api_key, model=args.model, base_url=args.base_url
            )
            print(explanation)
            return 0
        except Exception as e:  # surface but don't crash the whole tool
            print(f"[explain failed] {e}", file=sys.stderr)
            return 1

    if not git_data.is_git_repo(args.repo):
        print(
            f"GitLore: '{args.repo}' is not a git repository.\n"
            "Run gitlore inside a git repo, or pass --repo PATH.",
            file=sys.stderr,
        )
        return 1

    try:
        stats = _stats_from_args(args)
    except RuntimeError as e:
        print(f"GitLore error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(_to_dict(stats), indent=2))
        return 0

    if args.html:
        html = report.html_report(stats, top=max(args.top, 50))
        with open(args.html, "w", encoding="utf-8") as fh:
            fh.write(html)
        print(f"HTML report written to {args.html}")
        return 0

    if args.tui:
        from . import tui

        tui.run_tui(stats)
        return 0

    print(report.text_summary(stats, top=args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

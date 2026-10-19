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
    p.add_argument("--top", type=int, default=15, help="Number of rows to show")
    p.add_argument("--since", default=None, help="Only consider commits since (e.g. 2024-01-01)")
    p.add_argument("--max-count", type=int, default=None, help="Limit number of commits parsed")
    p.add_argument("--html", metavar="PATH", help="Write a standalone HTML report to PATH")
    p.add_argument("--tui", action="store_true", help="Open the interactive terminal UI")
    p.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    p.add_argument("--no-color", action="store_true", help="Disable colored output")
    p.add_argument(
        "--diff",
        metavar="RANGE",
        help="Pre-merge review mode: rank changed files in a git range "
        "(e.g. main...HEAD) by review attention.",
    )
    p.add_argument(
        "--skip",
        metavar="SUBSTR",
        help="Comma-separated extra path substrings to ignore (e.g. docs,tests).",
    )
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


def _skip_list(args: argparse.Namespace) -> list[str]:
    skip = list(DEFAULT_SKIP)
    extra = getattr(args, "skip", None)
    if extra:
        skip.extend(s.strip() for s in extra.split(",") if s.strip())
    return skip


def _use_rich(args: argparse.Namespace) -> bool:
    return not args.no_color and sys.stdout.isatty()


def _console(args: argparse.Namespace):
    from rich.console import Console

    return Console(no_color=args.no_color, emoji=False)


def _stats_from_args(args: argparse.Namespace) -> analysis.RepoStats:
    commits = git_data.get_commits(
        repo=args.repo, since=args.since, max_count=args.max_count
    )
    return build_stats(
        commits, repo=args.repo, top=args.top or None, skip_patterns=_skip_list(args)
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


def _diff_to_dict(review: analysis.DiffReview) -> dict:
    return {
        "repo": review.repo,
        "diff_range": review.diff_range,
        "files_changed": len(review.items),
        "total_added": review.total_added,
        "total_deleted": review.total_deleted,
        "items": [
            {
                "path": i.path,
                "added": i.added,
                "deleted": i.deleted,
                "commits": i.commits,
                "complexity": i.complexity,
                "risk": round(i.risk, 2),
                "attention": round(i.attention, 2),
            }
            for i in review.items
        ],
    }


def _run_diff(args: argparse.Namespace) -> int:
    try:
        commits = git_data.get_commits(repo=args.repo)
        diff_files = git_data.get_diff_files(args.repo, args.diff)
    except RuntimeError as e:
        print(f"GitLore error: {e}", file=sys.stderr)
        return 1
    review = analysis.build_diff_review(
        commits,
        diff_files,
        repo=args.repo,
        diff_range=args.diff,
        top=args.top or None,
        skip_patterns=_skip_list(args),
    )
    if args.json:
        print(json.dumps(_diff_to_dict(review), indent=2))
        return 0
    if args.html:
        with open(args.html, "w", encoding="utf-8") as fh:
            fh.write(report.html_diff_report(review, top=max(args.top, 50)))
        print(f"HTML review written to {args.html}")
        return 0
    if _use_rich(args):
        _console(args).print(report.render_diff_review(review, top=args.top))
    else:
        print(report.text_diff_review(review, top=args.top))
    return 0


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

    if args.diff:
        return _run_diff(args)

    try:
        stats = _stats_from_args(args)
    except RuntimeError as e:
        print(f"GitLore error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(_to_dict(stats), indent=2))
        return 0

    if args.html:
        with open(args.html, "w", encoding="utf-8") as fh:
            fh.write(report.html_report(stats, top=max(args.top, 50)))
        print(f"HTML report written to {args.html}")
        return 0

    if args.tui:
        from . import tui

        tui.run_tui(stats)
        return 0

    if _use_rich(args):
        _console(args).print(report.render_summary(stats, top=args.top))
    else:
        print(report.text_summary(stats, top=args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

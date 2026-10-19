"""Aggregate git history into the metrics GitLore reports."""
from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from .git_data import Commit, FileChange

# Language-agnostic control-flow keywords used as a complexity proxy.
_CONTROL = re.compile(
    r"\b(if|else|elif|for|while|do|switch|case|catch|except|finally|"
    r"return|break|continue|&&|\|\||\?)\b"
)
_DEF = re.compile(r"\b(def|function|func|class|struct|impl|method)\b")


@dataclass
class FileMetric:
    path: str
    commits: int = 0
    added: int = 0
    deleted: int = 0
    churn: int = 0  # added + deleted (total touch size)
    complexity: int = 0
    risk: float = 0.0

    @property
    def lines(self) -> int:
        return self.added  # approximated by historical additions


@dataclass
class Contributor:
    name: str
    commits: int = 0
    added: int = 0
    deleted: int = 0


@dataclass
class TimelinePoint:
    week: str
    commits: int = 0


@dataclass
class DiffReviewItem:
    path: str
    added: int = 0
    deleted: int = 0
    diff_churn: int = 0  # lines changed in THIS diff
    commits: int = 0      # historical commit count
    complexity: int = 0
    risk: float = 0.0
    attention: float = 0.0  # diff_churn weighted by historical risk


@dataclass
class DiffReview:
    repo: str
    diff_range: str
    items: list[DiffReviewItem] = field(default_factory=list)
    total_added: int = 0
    total_deleted: int = 0


@dataclass
class RepoStats:
    repo: str
    total_commits: int = 0
    total_authors: int = 0
    total_files: int = 0
    files: list[FileMetric] = field(default_factory=list)
    contributors: list[Contributor] = field(default_factory=list)
    timeline: list[TimelinePoint] = field(default_factory=list)
    first_commit: Optional[datetime] = None
    last_commit: Optional[datetime] = None


def estimate_complexity(path: str) -> int:
    """Heuristic complexity of the current working-tree file.

    Counts control-flow keywords and definitions. This is intentionally
    simple and language-agnostic; it is a *proxy*, not a real metric.
    """
    p = Path(path)
    if not p.exists() or not p.is_file():
        return 0
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return 0
    control = len(_CONTROL.findall(text))
    definitions = len(_DEF.findall(text))
    return control + definitions * 2


def _aggregate_file_metrics(
    commits: Iterable[Commit], repo: str, skip: list[str]
) -> dict[str, FileMetric]:
    """Per-file churn/complexity/risk from full history (shared by both modes)."""
    file_map: dict[str, FileMetric] = {}
    for c in commits:
        for ch in c.changes:
            if _should_skip(ch.path, skip):
                continue
            fm = file_map.get(ch.path)
            if fm is None:
                fm = FileMetric(path=ch.path)
                file_map[ch.path] = fm
            fm.commits += 1
            fm.added += ch.added
            fm.deleted += ch.deleted
            fm.churn += ch.added + ch.deleted
    repo_root = Path(repo).resolve()
    for fm in file_map.values():
        fm.complexity = estimate_complexity(str(repo_root / fm.path))
        # risk blends how often a file changes with how hard it is to reason about
        fm.risk = fm.commits * math.log1p(fm.complexity) * math.log1p(fm.churn)
    return file_map


def build_stats(
    commits: Iterable[Commit],
    repo: str = ".",
    top: Optional[int] = None,
    skip_patterns: Optional[list[str]] = None,
) -> RepoStats:
    skip = skip_patterns or []
    commits = list(commits)
    file_map = _aggregate_file_metrics(commits, repo, skip)

    contrib_map: dict[str, Contributor] = defaultdict(lambda: Contributor(name=""))
    week_map: dict[str, int] = defaultdict(int)
    first: Optional[datetime] = None
    last: Optional[datetime] = None
    for c in commits:
        if first is None or c.date < first:
            first = c.date
        if last is None or c.date > last:
            last = c.date
        contrib = contrib_map[c.author]
        contrib.name = c.author
        contrib.commits += 1
        wk = c.date.isocalendar()
        week_map[f"{wk[0]}-W{wk[1]:02d}"] += 1
        for ch in c.changes:
            if _should_skip(ch.path, skip):
                continue
            contrib.added += ch.added
            contrib.deleted += ch.deleted

    files = sorted(file_map.values(), key=lambda f: f.risk, reverse=True)
    contributors = sorted(contrib_map.values(), key=lambda c: c.commits, reverse=True)
    timeline = [TimelinePoint(week=w, commits=n) for w, n in sorted(week_map.items())]

    stats = RepoStats(
        repo=repo,
        total_commits=len(commits),
        total_authors=len(contrib_map),
        total_files=len(file_map),
        files=files,
        contributors=contributors,
        timeline=timeline,
        first_commit=first,
        last_commit=last,
    )
    if top:
        stats.files = stats.files[:top]
    return stats


def build_diff_review(
    commits: Iterable[Commit],
    diff_files: Iterable[FileChange],
    repo: str = ".",
    diff_range: str = "",
    top: Optional[int] = None,
    skip_patterns: Optional[list[str]] = None,
) -> DiffReview:
    """Rank the files in a specific diff by "review attention".

    attention = size of this change weighted by the file's historical risk,
    so a big edit to a fragile file outranks a big edit to a stable one.
    """
    skip = skip_patterns or []
    file_map = _aggregate_file_metrics(list(commits), repo, skip)
    items: list[DiffReviewItem] = []
    total_add = total_del = 0
    for fc in diff_files:
        if _should_skip(fc.path, skip):
            continue
        fm = file_map.get(fc.path)
        item = DiffReviewItem(
            path=fc.path,
            added=fc.added,
            deleted=fc.deleted,
            diff_churn=fc.added + fc.deleted,
            commits=fm.commits if fm else 0,
            complexity=fm.complexity if fm else 0,
            risk=fm.risk if fm else 0.0,
        )
        item.attention = item.diff_churn * (1.0 + math.log1p(item.risk))
        items.append(item)
        total_add += fc.added
        total_del += fc.deleted
    items.sort(key=lambda i: i.attention, reverse=True)
    review = DiffReview(
        repo=repo,
        diff_range=diff_range,
        items=items,
        total_added=total_add,
        total_deleted=total_del,
    )
    if top:
        review.items = review.items[:top]
    return review


def _should_skip(path: str, patterns: list[str]) -> bool:
    lowered = path.lower()
    for pat in patterns:
        if pat in lowered:
            return True
    return False

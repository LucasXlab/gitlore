"""Parse git history into structured data.

Uses only the `git` CLI via subprocess so there are no heavy dependencies
and behavior matches what the user already has installed.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

COMMIT_SEP = "__GITLORE_COMMIT__"


@dataclass
class FileChange:
    path: str
    added: int
    deleted: int


@dataclass
class Commit:
    hash: str
    author: str
    email: str
    date: datetime
    message: str
    changes: list[FileChange] = field(default_factory=list)


def _run(args: list[str], repo: str = ".") -> str:
    result = subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git command failed: {' '.join(args)}\n{result.stderr.strip()}"
        )
    return result.stdout


def is_git_repo(repo: str = ".") -> bool:
    try:
        out = subprocess.run(
            ["git", "-C", repo, "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False,
        )
        return out.returncode == 0 and out.stdout.strip() == "true"
    except FileNotFoundError:
        return False


def _parse_log(raw: str) -> list[Commit]:
    commits: list[Commit] = []
    # Split into per-commit chunks. The first chunk is empty (leading sep).
    chunks = raw.split(COMMIT_SEP)
    for chunk in chunks[1:]:
        lines = chunk.split("\n")
        if not lines:
            continue
        meta = lines[0]
        # meta: H|an|ae|ad|s
        parts = meta.split("|")
        if len(parts) < 5:
            continue
        h, an, ae, ad, subject = parts[0], parts[1], parts[2], parts[3], "|".join(parts[4:])
        try:
            dt = datetime.fromisoformat(ad)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            dt = datetime.now(timezone.utc)
        changes: list[FileChange] = []
        for line in lines[1:]:
            if not line.strip():
                continue
            fields = line.split("\t")
            if len(fields) < 3:
                continue
            add_s, del_s, path = fields[0], fields[1], fields[2]
            added = 0 if add_s == "-" else _to_int(add_s)
            deleted = 0 if del_s == "-" else _to_int(del_s)
            changes.append(FileChange(path=path, added=added, deleted=deleted))
        commits.append(
            Commit(
                hash=h,
                author=an,
                email=ae,
                date=dt,
                message=subject.strip(),
                changes=changes,
            )
        )
    return commits


def _to_int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 0


def get_commits(
    repo: str = ".",
    since: Optional[str] = None,
    max_count: Optional[int] = None,
) -> list[Commit]:
    """Return all commits (optionally filtered) with per-file numstat."""
    args = [
        "log",
        "--numstat",
        "--date=iso-strict",
        f"--pretty=format:{COMMIT_SEP}%H|%an|%ae|%ad|%s",
    ]
    if since:
        args.append(f"--since={since}")
    if max_count:
        args.append(f"--max-count={max_count}")
    raw = _run(args, repo=repo)
    return _parse_log(raw)


def get_commit_diff(repo: str, commit_hash: str) -> str:
    """Return the textual diff of a single commit (used by the AI explainer)."""
    # The explainer needs the patch, not the author's identity or commit metadata.
    # Avoid invoking user-configured diff helpers while preparing outbound data.
    return _run(
        ["show", "--format=", "--no-ext-diff", "--no-textconv", "--no-color", commit_hash],
        repo=repo,
    )


def get_diff_files(repo: str, diff_range: str) -> list[FileChange]:
    """Return per-file add/delete counts for a diff range.

    `diff_range` is any git rev range accepted by `git diff`, e.g.
    ``main...HEAD`` (what a PR would merge) or ``HEAD~1..HEAD``.
    """
    raw = _run(["diff", "--numstat", diff_range], repo=repo)
    changes: list[FileChange] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) < 3:
            continue
        add_s, del_s, path = fields[0], fields[1], fields[2]
        changes.append(
            FileChange(
                path=path,
                added=0 if add_s == "-" else _to_int(add_s),
                deleted=0 if del_s == "-" else _to_int(del_s),
            )
        )
    return changes


def current_branch(repo: str = ".") -> str:
    return _run(["rev-parse", "--abbrev-ref", "HEAD"], repo=repo).strip()


def repo_name(repo: str = ".") -> str:
    try:
        url = _run(["config", "--get", "remote.origin.url"], repo=repo).strip()
        if url:
            # strip .git and trailing path
            name = url.rstrip("/")
            if name.endswith(".git"):
                name = name[:-4]
            return name.split("/")[-1]
    except Exception:
        pass
    return Path(repo).resolve().name

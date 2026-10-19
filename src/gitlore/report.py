"""Plain-text and HTML reporting for GitLore."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .analysis import RepoStats

_SPARK = "▁▂▃▄▅▆▇█"


def sparkline(values: list[int], width: int = 40) -> str:
    if not values:
        return ""
    lo, hi = min(values), max(values)
    if hi == lo:
        return _SPARK[-1] * min(width, len(values))
    n = min(width, max(len(values), 1))
    step = max(1, len(values) / n)
    out = []
    for i in range(n):
        idx = int(i * step)
        if idx >= len(values):
            idx = len(values) - 1
        v = values[idx]
        bucket = int((v - lo) / (hi - lo) * (len(_SPARK) - 1))
        out.append(_SPARK[bucket])
    return "".join(out)


def _fmt_dt(dt: Optional[datetime]) -> str:
    if dt is None:
        return "n/a"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%d")


def text_summary(stats: RepoStats, top: int = 15) -> str:
    lines = []
    lines.append("GitLore — codebase story")
    lines.append("=" * 60)
    lines.append(f"Repository : {stats.repo}")
    lines.append(f"Commits    : {stats.total_commits}")
    lines.append(f"Authors    : {stats.total_authors}")
    lines.append(f"Files      : {stats.total_files}")
    if stats.first_commit:
        lines.append(
            f"Range      : {_fmt_dt(stats.first_commit)} → {_fmt_dt(stats.last_commit)}"
        )
    lines.append("")
    lines.append(f"Activity (commits/week): {sparkline([t.commits for t in stats.timeline])}")
    lines.append("")
    lines.append(f"Top {top} risk hotspots (churn × complexity):")
    lines.append("-" * 60)
    for i, f in enumerate(stats.files[:top], 1):
        lines.append(
            f"{i:>2}. {f.path[:42]:<42} "
            f"risk={f.risk:8.1f} commits={f.commits:<4} "
            f"churn={f.churn:<7} cx={f.complexity}"
        )
    lines.append("")
    lines.append("Top contributors:")
    lines.append("-" * 60)
    for c in stats.contributors[:10]:
        lines.append(f"  {c.name[:30]:<30} commits={c.commits:<5} +{c.added}/-{c.deleted}")
    return "\n".join(lines)


def text_diff_review(review: "DiffReview", top: int = 15) -> str:
    lines = [
        f"GitLore — pre-merge review of {review.diff_range}",
        "=" * 60,
        f"Files changed: {len(review.items)}  +{review.total_added}/-{review.total_deleted}",
        "",
        f"Top {top} files to review (attention = change size × historical risk):",
        "-" * 60,
    ]
    for i, it in enumerate(review.items[:top], 1):
        lines.append(
            f"{i:>2}. {it.path[:40]:<40} attn={it.attention:8.1f} "
            f"+{it.added}/-{it.deleted} commits={it.commits} cx={it.complexity}"
        )
    return "\n".join(lines)


def _risk_style(value: float, lo: float, hi: float) -> str:
    if hi <= lo:
        return "green"
    r = (value - lo) / (hi - lo)
    if r > 0.75:
        return "bold red"
    if r > 0.5:
        return "orange3"
    if r > 0.25:
        return "yellow"
    return "green"


def render_summary(stats: RepoStats, top: int = 15):
    """Rich renderable of the full codebase story (colored)."""
    from rich import box
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    files = stats.files[:top]
    lo = min((f.risk for f in files), default=0.0)
    hi = max((f.risk for f in files), default=1.0)

    head = Table.grid(padding=(0, 1))
    head.add_row(Text(f"Repository: {stats.repo}", style="cyan"))
    head.add_row(
        f"Commits: {stats.total_commits}   Authors: {stats.total_authors}   Files: {stats.total_files}"
    )
    if stats.first_commit:
        head.add_row(f"Range: {_fmt_dt(stats.first_commit)} → {_fmt_dt(stats.last_commit)}")
    head.add_row(
        Text(
            f"Activity (commits/week): {sparkline([t.commits for t in stats.timeline])}",
            style="blue",
        )
    )

    tbl = Table(
        title=f"Top {top} risk hotspots (churn × complexity)",
        box=box.SIMPLE_HEAVY,
        title_style="bold",
    )
    for col, just in (("#", "right"), ("File", "left"), ("Risk", "right"),
                      ("Commits", "right"), ("Churn", "right"), ("Cx", "right")):
        tbl.add_column(col, justify=just)
    for i, f in enumerate(files, 1):
        tbl.add_row(
            str(i),
            f.path,
            Text(f"{f.risk:.1f}", style=_risk_style(f.risk, lo, hi)),
            str(f.commits),
            str(f.churn),
            str(f.complexity),
        )

    ctab = Table(title="Top contributors", box=box.SIMPLE_HEAVY, title_style="bold")
    ctab.add_column("Author")
    ctab.add_column("Commits", justify="right")
    ctab.add_column("Added", justify="right")
    ctab.add_column("Deleted", justify="right")
    for c in stats.contributors[:10]:
        ctab.add_row(c.name, str(c.commits), f"+{c.added}", f"-{c.deleted}")

    return Group(
        Panel(head, title="GitLore — codebase story", border_style="cyan"),
        tbl,
        ctab,
    )


def render_diff_review(review: "DiffReview", top: int = 15):
    """Rich renderable of the pre-merge review (colored)."""
    from rich import box
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    items = review.items[:top]
    lo = min((i.attention for i in items), default=0.0)
    hi = max((i.attention for i in items), default=1.0)

    head = Table.grid(padding=(0, 1))
    head.add_row(Text(f"Reviewing: {review.diff_range}", style="cyan"))
    head.add_row(
        f"Files changed: {len(review.items)}   +{review.total_added}/-{review.total_deleted}"
    )

    tbl = Table(
        title="Pre-merge review — look here first",
        box=box.SIMPLE_HEAVY,
        title_style="bold",
    )
    for col, just in (("#", "right"), ("File", "left"), ("Δ change", "right"),
                      ("Hist.commits", "right"), ("Cx", "right"), ("Attention", "right")):
        tbl.add_column(col, justify=just)
    for i, it in enumerate(items, 1):
        tbl.add_row(
            str(i),
            it.path,
            f"+{it.added}/-{it.deleted}",
            str(it.commits),
            str(it.complexity),
            Text(f"{it.attention:.1f}", style=_risk_style(it.attention, lo, hi)),
        )
    return Group(
        Panel(head, title="GitLore — pre-merge review", border_style="cyan"), tbl
    )


def _heat(value: float, max_value: float) -> str:
    if max_value <= 0:
        return "#1e293b"
    ratio = value / max_value
    # from cool (low) to warm (high)
    r = int(30 + ratio * 200)
    g = int(80 - ratio * 40)
    b = int(120 - ratio * 80)
    return f"#{r:02x}{g:02x}{b:02x}"


def html_report(stats: RepoStats, top: int = 50) -> str:
    max_risk = max((f.risk for f in stats.files), default=1)
    files_rows = []
    for f in stats.files[:top]:
        color = _heat(f.risk, max_risk)
        files_rows.append(
            f"<tr style='background:{color}'>"
            f"<td>{_esc(f.path)}</td>"
            f"<td>{f.risk:.1f}</td>"
            f"<td>{f.commits}</td>"
            f"<td>{f.churn}</td>"
            f"<td>{f.complexity}</td></tr>"
        )
    contrib_rows = "".join(
        f"<tr><td>{_esc(c.name)}</td><td>{c.commits}</td>"
        f"<td>+{c.added}</td><td>-{c.deleted}</td></tr>"
        for c in stats.contributors[:15]
    )
    spark = sparkline([t.commits for t in stats.timeline], width=60)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GitLore report — {_esc(stats.repo)}</title>
<style>
 body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#0f172a;color:#e2e8f0;padding:32px}}
 h1{{font-size:22px}} h2{{font-size:16px;margin-top:28px;border-left:4px solid #38bdf8;padding-left:8px}}
 table{{border-collapse:collapse;width:100%;font-size:13px;margin-top:8px}}
 th,td{{text-align:left;padding:6px 10px}}
 th{{color:#94a3b8;border-bottom:1px solid #334155}}
 .spark{{font-size:20px;letter-spacing:2px;color:#38bdf8;margin:6px 0}}
 .meta{{color:#94a3b8;font-size:13px}}
 .card{{background:#1e293b;border-radius:10px;padding:16px;margin-top:12px}}
</style></head><body>
<h1>GitLore — the story of <span style="color:#38bdf8">{_esc(stats.repo)}</span></h1>
<p class="meta">Generated by GitLore · {stats.total_commits} commits · {stats.total_authors} authors · {stats.total_files} files · {_fmt_dt(stats.first_commit)} → {_fmt_dt(stats.last_commit)}</p>
<div class="card"><h2>Activity (commits / week)</h2><div class="spark">{spark}</div></div>
<div class="card"><h2>Risk hotspots (churn × complexity)</h2>
<table><tr><th>File</th><th>Risk</th><th>Commits</th><th>Churn</th><th>Complexity</th></tr>
{''.join(files_rows)}</table></div>
<div class="card"><h2>Contributors</h2>
<table><tr><th>Author</th><th>Commits</th><th>Added</th><th>Deleted</th></tr>
{contrib_rows}</table></div>
</body></html>"""


def html_diff_report(review: "DiffReview", top: int = 50) -> str:
    max_att = max((i.attention for i in review.items), default=1)
    rows = "".join(
        f"<tr style='background:{_heat(i.attention, max_att)}'>"
        f"<td>{_esc(i.path)}</td>"
        f"<td>+{i.added}/-{i.deleted}</td>"
        f"<td>{i.commits}</td>"
        f"<td>{i.complexity}</td>"
        f"<td>{i.attention:.1f}</td></tr>"
        for i in review.items[:top]
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GitLore review — {_esc(review.diff_range)}</title>
<style>
 body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#0f172a;color:#e2e8f0;padding:32px}}
 h1{{font-size:22px}} h2{{font-size:16px;margin-top:28px;border-left:4px solid #38bdf8;padding-left:8px}}
 table{{border-collapse:collapse;width:100%;font-size:13px;margin-top:8px}}
 th,td{{text-align:left;padding:6px 10px}}
 th{{color:#94a3b8;border-bottom:1px solid #334155}}
 .meta{{color:#94a3b8;font-size:13px}}
 .card{{background:#1e293b;border-radius:10px;padding:16px;margin-top:12px}}
</style></head><body>
<h1>GitLore — pre-merge review of <span style="color:#38bdf8">{_esc(review.diff_range)}</span></h1>
<p class="meta">{len(review.items)} files changed · +{review.total_added}/-{review.total_deleted}</p>
<div class="card"><h2>Review attention (change size × historical risk)</h2>
<table><tr><th>File</th><th>Δ change</th><th>Hist.commits</th><th>Complexity</th><th>Attention</th></tr>
{rows}</table></div>
</body></html>"""


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

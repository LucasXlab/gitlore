"""Interactive Terminal UI for GitLore (Textual).

Lazily imported by the CLI only when `--tui` is requested, so the core
features work even if Textual is not installed.
"""
from __future__ import annotations

from .analysis import RepoStats
from .report import sparkline


def run_tui(stats: RepoStats) -> None:
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import DataTable, Header, Footer, Static, TabbedContent, TabPane

    class GitLoreApp(App):
        CSS = """
        DataTable { height: 1fr; }
        .spark { color: $accent; }
        """
        BINDINGS = [("q", "quit", "Quit")]

        def compose(self) -> ComposeResult:
            yield Header()
            with TabbedContent("Overview", "Files", "Contributors", "Timeline"):
                with TabPane("Overview"):
                    yield Static(self._overview(), id="overview")
                with TabPane("Files"):
                    yield DataTable(id="files")
                with TabPane("Contributors"):
                    yield DataTable(id="contrib")
                with TabPane("Timeline"):
                    yield Static(self._timeline(), id="timeline")
            yield Footer()

        def on_mount(self) -> None:
            ft = self.query_one("#files", DataTable)
            ft.add_columns("File", "Risk", "Commits", "Churn", "Complexity")
            for f in stats.files[:200]:
                ft.add_row(f.path, f"{f.risk:.1f}", str(f.commits), str(f.churn), str(f.complexity))
            ct = self.query_one("#contrib", DataTable)
            ct.add_columns("Author", "Commits", "Added", "Deleted")
            for c in stats.contributors[:50]:
                ct.add_row(c.name, str(c.commits), f"+{c.added}", f"-{c.deleted}")

        def _overview(self) -> str:
            return (
                f"[b]GitLore — {stats.repo}[/b]\n"
                f"Commits: {stats.total_commits}  Authors: {stats.total_authors}  "
                f"Files: {stats.total_files}\n"
                f"Activity: {sparkline([t.commits for t in stats.timeline])}"
            )

        def _timeline(self) -> str:
            lines = ["[b]Commits per week[/b]"]
            for t in stats.timeline[-40:]:
                lines.append(f"{t.week}: {sparkline([t.commits], width=1) or '·'} {t.commits}")
            return "\n".join(lines)

    GitLoreApp().run()

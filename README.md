<p align="center">
  <h1 align="center">GitLore</h1>
  <p align="center"><b>Visualize your codebase's story from git history — churn, complexity hotspots, contributors, and timeline. Zero config.</b></p>
  <p align="center">
    <a href="https://github.com/gitlore/gitlore/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
    <a href="https://pypi.org/project/gitlore/"><img alt="PyPI" src="https://img.shields.io/pypi/v/gitlore.svg"></a>
    <a href="https://github.com/gitlore/gitlore/actions"><img alt="CI" src="https://github.com/gitlore/gitlore/actions/workflows/ci.yml/badge.svg"></a>
  </p>
</p>

![GitLore terminal demo](https://raw.githubusercontent.com/gitlore/gitlore/main/assets/demo.gif)

## Install

```bash
pip install gitlore
```

## Use it (zero config)

```bash
cd any-git-repo
gitlore
```

That's it. No config file, no API key, no server. GitLore reads your git history
and prints the story of your codebase: where the churn is, which files are
riskiest to change, who built what, and how activity evolved over time.

Want a shareable report? One flag:

```bash
gitlore --html report.html
```

## Why

Every developer has stared at an unfamiliar repo — or a 200-file PR — and
thought *"where do I even start?"* GitLore answers that in one command by
turning raw `git log` into actionable signals:

- **Risk hotspots** — files ranked by `churn × complexity`, i.e. things that
  change often *and* are hard to reason about. The best places to review or
  refactor first.
- **Contributor map** — who owns what, by commit and by lines.
- **Activity timeline** — commits-per-week sparkline, so you can see bursts,
  stalls, and bus-factor at a glance.
- **Optional AI explainer** — bring your own key and get a plain-English
  summary of any commit (`gitlore --explain HEAD`).

## Features

- 🚀 **Zero config** — runs on the repo you're already in.
- 🔥 **Risk hotspots** ranked by churn × complexity.
- 👥 **Contributor breakdown** (commits, additions, deletions).
- 📈 **Activity sparkline** across the project's lifetime.
- 🖥️ **Interactive TUI** (`--tui`) built with [Textual](https://textual.textualize.io).
- 📄 **Standalone HTML report** (`--html`) with a heatmap — no JS, no tracking.
- 🤖 **BYOK AI explainer** (`--explain`) for any commit, OpenAI-compatible.
- 📦 **Machine-readable JSON** (`--json`) for piping into other tools.
- 🪶 **Pure Python + `git`**, no heavy native deps for the core.

## Comparison

| | GitLore | gource | gitk / tig | VS Code Git Graph |
|---|---|---|---|---|
| Zero config | ✅ | ❌ (needs OpenGL) | ⚠️ GUI / log only | ❌ (needs editor) |
| Risk hotspots | ✅ | ❌ | ❌ | ❌ |
| Contributor map | ✅ | ⚠️ visual only | ❌ | ⚠️ |
| HTML report | ✅ | ❌ | ❌ | ❌ |
| AI explain | ✅ (BYOK) | ❌ | ❌ | ❌ |
| Terminal-first | ✅ | ❌ | ✅ | ❌ |

## Commands

```bash
gitlore                         # pretty terminal summary (default)
gitlore --top 30                # show more hotspots
gitlore --since 2025-01-01      # only recent history
gitlore --html report.html      # standalone shareable report
gitlore --tui                   # interactive browser
gitlore --json                  # machine-readable output
gitlore --explain HEAD          # plain-English summary (needs key)
gitlore --repo /path/to/repo    # analyze another repo
```

The AI explainer works with any OpenAI-compatible endpoint:

```bash
export OPENAI_API_KEY=sk-...
gitlore --explain abc123 --model gpt-4o-mini
# or point at a local gateway:
gitlore --explain HEAD --base-url http://localhost:11434/v1
```

## FAQ

**Does GitLore send my code anywhere?**
No. The core runs entirely locally on your machine. The `--explain` feature
only contacts the API *you* configure, using *your* key, and only sends the
single commit diff you asked about.

**What about private repos?**
GitLore only reads local git metadata and your working tree. Nothing leaves
your machine unless you opt into `--explain`.

**Does it need a server or database?**
No server, no database, no config file. Pure CLI/TUI.

**Will it be slow on big repos?**
GitLore streams `git log` and ignores `node_modules`, `dist`, `.venv`, etc.
by default. For very large histories, `--since` or `--max-count` narrow the scope.

**Which Python versions are supported?**
3.10+.

## Roadmap

- [ ] Language-aware complexity (real cyclomatic estimate per ecosystem)
- [ ] Branch / PR-focused diff risk before you hit "merge"
- [ ] `--tui` drill-down into a single file's history
- [ ] Export to SVG/PNG for slides
- [ ] GitLore as a pre-commit / CI check (fail on new hotspots)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Good first issues are tagged
[`good first issue`](https://github.com/gitlore/gitlore/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

## License

[MIT](LICENSE)

# Changelog

## [Unreleased]

### Added
- `--diff RANGE` pre-merge review: ranks the files in a git range by
  "review attention" (change size × historical risk). Supports `--json`
  and `--html`.
- `--skip` to extend the default ignore list.
- `--no-color` for plain output; colored `rich` output is used automatically
  when stdout is a terminal.

## [0.1.0] - 2026-10-16

Initial public release of GitLore.

### Added
- `gitlore` terminal summary: risk hotspots (churn × complexity), contributor
  map, and commits-per-week sparkline.
- `--html PATH` to export a standalone, tracking-free HTML heatmap report.
- `--tui` interactive browser (Textual).
- `--json` machine-readable output for piping into other tools.
- `--explain <commit>` optional bring-your-own-key AI summary, OpenAI-compatible
  (including local LLM gateways).
- `--repo`, `--top`, `--since`, `--max-count`, `--skip` options.
- Default skip list for heavy dirs (`node_modules`, `dist`, `.venv`, ...).
- Cross-platform CI (ubuntu/macos/windows × Python 3.10–3.13) and a PyPI
  publish workflow.

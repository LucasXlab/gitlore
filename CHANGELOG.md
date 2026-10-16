# Changelog

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

# Contributing to GitLore

Thanks for your interest! GitLore is a small, focused tool and welcomes
contributions of all sizes.

## Getting started

```bash
git clone https://github.com/gitlore/gitlore
cd gitlore
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

## How to contribute

1. Open an issue (or comment on an existing one) before a large change.
2. Fork, create a branch (`feat/...`, `fix/...`), make your change.
3. Add/Update tests — core logic must stay covered.
4. Run `pytest -q` and ensure it's green on your machine.
5. Open a PR with a clear description of *why* and *what*.

## Code style

- Pure Python 3.10+, type hints where helpful.
- Keep the core dependency-light: `rich` and `textual` only.
  The AI explainer and its `openai` dependency must stay optional/lazy.
- No network calls in the core path. Ever.

## Good first issues

See [`docs/good-first-issues.md`](docs/good-first-issues.md) for curated,
well-scoped tasks labeled `good first issue`.

## Code of conduct

Be kind. Assume good intent. We want this to be a welcoming project.

# Good First Issues

These are ready-to-post issues for new contributors. Each is scoped to be
achievable in a few hours and touches a single, well-understood area.

> Tip: post them with the `good first issue` label via
> `gh issue create --label "good first issue" -F <file>`.

---

### 1. Add a `--csv` export alongside `--json` / `--html`
**File:** `src/gitlore/cli.py`, `src/gitlore/report.py`
**Why:** Some users want to drop the hotspots table straight into a
spreadsheet.
**Task:** Add a `--csv PATH` flag that writes the file metrics as CSV.
Add a test in `tests/test_cli.py`.

### 2. Make the default skip list configurable via `--skip`
**File:** `src/gitlore/cli.py`, `src/gitlore/analysis.py`
**Why:** Monorepos have other heavy dirs (e.g. `packages/`, `artifacts/`).
**Task:** Add `--skip foo,bar` that extends `DEFAULT_SKIP`. Update tests.

### 3. Friendlier "no commits" message
**File:** `src/gitlore/cli.py`
**Why:** A fresh repo prints an empty summary that looks broken.
**Task:** Detect zero commits and print a helpful hint instead.

### 4. Colorize the terminal summary with `rich`
**File:** `src/gitlore/report.py`
**Why:** The current text summary is plain; a little color goes a long way.
**Task:** Use `rich` to color the hotspot ranks / sparkline. Keep it readable
on light terminals.

### 5. Document a one-line `pipx` install in the README
**File:** `README.md`
**Why:** `pipx` is the recommended way to install CLI tools globally.
**Task:** Add a `pipx install gitlore` line near the install section and note
the difference vs `pip install`.

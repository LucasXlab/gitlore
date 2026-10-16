# How GitLore computes "risk" (and why it's honest about being simple)

*Draft for launch-day post. Keep it factual; no hype.*

When you run `gitlore` in a repo, the first thing you see is a ranked list of
"risk hotspots." People immediately ask: *what does "risk" mean, and is it
real?*

Short answer: it's a transparent heuristic, not a crystal ball. Here's exactly
how it works.

## The two ingredients

For every file in your history, GitLore tracks two numbers:

1. **Churn** — how much the file has changed: the sum of lines added and
   deleted across all commits that touched it (`git log --numstat`).
2. **Commits** — how many times the file was touched.

And for the file as it exists *right now* in your working tree, a **complexity
proxy**: a language-agnostic count of control-flow keywords (`if`, `else`,
`for`, `while`, `try/except`, `switch/case`, `&&`, `||`, ...) plus a weight
for definitions (`def`, `class`, `function`, ...). This is a proxy, not a real
cyclomatic count — it's deliberately simple so GitLore stays dependency-light
and fast.

## The formula

```
risk = commits × log1p(complexity) × log1p(churn)
```

Why this shape?

- **commits** captures "this file changes a lot" — the classic defect-density
  signal (files that change often, keep changing).
- **log1p(complexity)** rewards files that are hard to reason about, but on a
  compressed scale so a 200-line tangle doesn't dwarf everything.
- **log1p(churn)** similarly compresses the size signal.

Multiplying means a file has to be *both* frequently touched *and* hard to
reason about to rank high. A file that's complex but never changes (a stable
config), or one that changes a lot but is trivial (a generated file), scores
lower than a file that is both.

## What it is NOT

- It's not a linter. It won't tell you the bug is on line 42.
- It's not a security scanner.
- It doesn't look at code *quality* beyond a crude complexity proxy.
- It ignores commit *semantics* — a one-line fix and a 500-line refactor count
  the same in churn.

The point is triage: *where should a human look first?* In our own repo, the
top hotspots were exactly the modules doing the real work (`analysis.py`,
`git_data.py`, `report.py`) — which is the sanity check you want.

## Honest limitations (and the roadmap)

The complexity proxy is crude and language-agnostic. On the roadmap:
real per-language cyclomatic analysis, and a branch/PR mode that scores *just
the diff you're about to merge*. Until then, treat the ranking as a well-lit
starting point, not a verdict.

That's the whole trick. One command, your own `git log`, no server, no key.

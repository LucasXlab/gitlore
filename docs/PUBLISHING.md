# Publishing GitLore to PyPI

Two ways. Both are one-click once set up — the repo already has
`.github/workflows/publish.yml`, which triggers on a GitHub **Release** or on
pushing a `v*` **tag**.

## Option A — PyPI Trusted Publishing (recommended, no token)

1. Go to https://pypi.org/manage/account/publishing/ and add a **Trusted
   Publisher**:
   - PyPI project name: `gitlore`
   - Owner: `LucasYanzy`
   - Repository name: `gitlore`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
2. On GitHub, draft a **Release** (tag `v0.1.0`) or push a tag:
   ```bash
   git tag v0.1.0 && git push origin v0.1.0
   ```
3. The workflow publishes to PyPI using an OIDC token — no secret needed.

## Option B — API token

1. Create a token at https://pypi.org/manage/account/token/ (scope: entire
   account or the `gitlore` project).
2. In the GitHub repo: Settings → Secrets → Actions → New repository secret
   `PYPI_API_TOKEN` with the token value.
3. Draft a Release / push a `v*` tag. The workflow uses the secret.

## Verify

```bash
pip install gitlore
gitlore --version   # should print 0.1.0
```

import json

from gitlore import cli


def test_cli_summary(sample_repo, capsys):
    rc = cli.main(["--repo", str(sample_repo)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "GitLore" in out
    assert "a.py" in out


def test_cli_json(sample_repo, capsys):
    rc = cli.main(["--repo", str(sample_repo), "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["total_commits"] == 7
    assert any(f["path"] == "a.py" for f in data["files"])


def test_cli_html(sample_repo, tmp_path, capsys):
    out_path = tmp_path / "report.html"
    rc = cli.main(["--repo", str(sample_repo), "--html", str(out_path)])
    assert rc == 0
    assert out_path.exists()
    assert "GitLore" in out_path.read_text()


def test_cli_not_a_repo(tmp_path, capsys):
    rc = cli.main(["--repo", str(tmp_path)])
    assert rc == 1
    assert "not a git repository" in capsys.readouterr().err.lower()


def test_cli_version(capsys):
    rc = cli.main(["--version"])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "0.1.0"


def test_cli_diff_json(sample_repo, capsys):
    rc = cli.main(["--repo", str(sample_repo), "--diff", "HEAD~3..HEAD", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["diff_range"] == "HEAD~3..HEAD"
    assert any(i["path"] == "a.py" for i in data["items"])


def test_cli_diff_text(sample_repo, capsys):
    rc = cli.main(["--repo", str(sample_repo), "--diff", "HEAD~3..HEAD"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "pre-merge review" in out
    assert "a.py" in out


def test_cli_skip(sample_repo, capsys):
    rc = cli.main(["--repo", str(sample_repo), "--skip", "a.py", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert all(not f["path"].endswith("a.py") for f in data["files"])


def test_cli_no_color(sample_repo, capsys):
    rc = cli.main(["--repo", str(sample_repo), "--no-color"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "GitLore" in out and "a.py" in out

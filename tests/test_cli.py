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

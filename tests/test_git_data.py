from gitlore import git_data


def test_is_git_repo(sample_repo):
    assert git_data.is_git_repo(str(sample_repo)) is True
    assert git_data.is_git_repo("/nonexistent/path/xyz") is False


def test_get_commits_parses_all(sample_repo):
    commits = git_data.get_commits(repo=str(sample_repo))
    assert len(commits) == 7  # 1 init + 5 updates + 1 add b
    for c in commits:
        assert c.hash
        assert c.author == "Dev One"
        assert c.date is not None
        assert isinstance(c.changes, list)


def test_get_commits_since(sample_repo):
    commits = git_data.get_commits(repo=str(sample_repo), since="2030-01-01")
    assert commits == []


def test_get_commit_diff(sample_repo):
    commits = git_data.get_commits(repo=str(sample_repo))
    # git log returns newest-first, so commits[0] is the most recent ("add b")
    diff = git_data.get_commit_diff(str(sample_repo), commits[0].hash)
    assert "b.py" in diff or "def g" in diff

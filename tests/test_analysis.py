from gitlore import analysis, git_data


def test_build_stats_basic(sample_repo):
    commits = git_data.get_commits(repo=str(sample_repo))
    stats = analysis.build_stats(commits, repo=str(sample_repo), top=10)
    assert stats.total_commits == 7
    assert stats.total_authors == 1
    # a.py touched 6 times (init + 5 updates), b.py once
    paths = {f.path for f in stats.files}
    assert "a.py" in paths and "b.py" in paths
    a = next(f for f in stats.files if f.path == "a.py")
    assert a.commits == 6
    # riskiest file should be a.py (high churn), not b.py
    assert stats.files[0].path == "a.py"
    assert a.risk >= next(f for f in stats.files if f.path == "b.py").risk


def test_timeline_present(sample_repo):
    commits = git_data.get_commits(repo=str(sample_repo))
    stats = analysis.build_stats(commits, repo=str(sample_repo))
    assert len(stats.timeline) >= 1
    assert sum(t.commits for t in stats.timeline) == 7


def test_complexity_estimate(sample_repo):
    b = sample_repo / "b.py"
    cx = analysis.estimate_complexity(str(b))
    assert cx > 0  # contains if/else/def


def test_skip_patterns(sample_repo):
    commits = git_data.get_commits(repo=str(sample_repo))
    stats = analysis.build_stats(
        commits, repo=str(sample_repo), skip_patterns=["b.py"]
    )
    assert all(not f.path.endswith("b.py") for f in stats.files)


def _diff_review(sample_repo, skip=None):
    commits = git_data.get_commits(repo=str(sample_repo))
    diff_files = git_data.get_diff_files(str(sample_repo), "HEAD~3..HEAD")
    return analysis.build_diff_review(
        commits, diff_files, repo=str(sample_repo),
        diff_range="HEAD~3..HEAD", skip_patterns=skip,
    )


def test_build_diff_review_basic(sample_repo):
    review = _diff_review(sample_repo)
    paths = {i.path for i in review.items}
    assert "a.py" in paths and "b.py" in paths
    # sorted by attention, descending
    atts = [i.attention for i in review.items]
    assert atts == sorted(atts, reverse=True)
    a = next(i for i in review.items if i.path == "a.py")
    assert a.commits >= 1  # carries historical context
    assert a.attention > 0
    assert review.total_added >= 0


def test_build_diff_review_skip(sample_repo):
    review = _diff_review(sample_repo, skip=["a.py"])
    assert all(not i.path.endswith("a.py") for i in review.items)
    assert any(i.path.endswith("b.py") for i in review.items)

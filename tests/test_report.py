from gitlore import analysis, git_data, report


def test_sparkline():
    assert report.sparkline([]) == ""
    s = report.sparkline([0, 5, 10])
    assert len(s) == 3
    assert all(ch in report._SPARK for ch in s)
    # monotonic increasing -> last char is the tallest bucket
    assert s[-1] == report._SPARK[-1]


def test_text_summary(sample_repo):
    commits = git_data.get_commits(repo=str(sample_repo))
    stats = analysis.build_stats(commits, repo=str(sample_repo))
    text = report.text_summary(stats)
    assert "GitLore" in text
    assert "a.py" in text
    assert "Dev One" in text


def test_html_report(sample_repo):
    commits = git_data.get_commits(repo=str(sample_repo))
    stats = analysis.build_stats(commits, repo=str(sample_repo))
    html = report.html_report(stats)
    assert html.startswith("<!doctype html>")
    assert "GitLore" in html
    assert "a.py" in html


def _review(sample_repo):
    commits = git_data.get_commits(repo=str(sample_repo))
    diff_files = git_data.get_diff_files(str(sample_repo), "HEAD~3..HEAD")
    return analysis.build_diff_review(
        commits, diff_files, repo=str(sample_repo), diff_range="HEAD~3..HEAD"
    )


def test_text_diff_review(sample_repo):
    text = report.text_diff_review(_review(sample_repo))
    assert "pre-merge review" in text
    assert "a.py" in text


def test_html_diff_report(sample_repo):
    html = report.html_diff_report(_review(sample_repo))
    assert html.startswith("<!doctype html>")
    assert "a.py" in html
    assert "Attention" in html

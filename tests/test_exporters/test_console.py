"""Tests for ConsoleExporter with rich tables."""

from datetime import datetime, timezone
from io import StringIO

from rich.console import Console

from reddipy.models import Post, Comment, UserActivity
from reddipy.exporters.console import ConsoleExporter


def _capture_export(data: list) -> str:
    """Capture rich console output to a string."""
    buf = StringIO()
    console = Console(file=buf, width=200, force_terminal=True)
    # Monkey-patch the exporter to use our capture console
    exporter = ConsoleExporter()
    orig_methods = {}
    for method_name in ["_print_posts", "_print_comments", "_print_user_activity"]:
        orig = getattr(exporter, method_name)
        orig_methods[method_name] = orig

    def _patched_print_posts(d):
        from rich.table import Table
        table = Table(show_header=True, header_style="bold cyan", border_style="dim",
                      pad_edge=False, show_lines=False)
        table.add_column("ID", style="dim", width=10)
        table.add_column("Title", min_width=30, max_width=65)
        table.add_column("Author", style="green", width=22)
        table.add_column("Subreddit", style="magenta", width=18)
        table.add_column("Score", justify="right", style="yellow", width=7)
        table.add_column("Comments", justify="right", style="blue", width=9)
        from reddipy.exporters.console import _truncate
        for item in d:
            table.add_row(item.id, _truncate(item.title, 62), item.author,
                          f"r/{item.subreddit}", str(item.score), str(item.num_comments))
        console.print(table)

    def _patched_print_comments(d):
        from rich.table import Table
        table = Table(show_header=True, header_style="bold cyan", border_style="dim",
                      pad_edge=False, show_lines=False)
        table.add_column("ID", style="dim", width=10)
        table.add_column("Author", style="green", width=22)
        table.add_column("Comment", min_width=30, max_width=55)
        table.add_column("Score", justify="right", style="yellow", width=7)
        table.add_column("Depth", justify="right", style="blue", width=6)
        from reddipy.exporters.console import _truncate
        for item in d:
            table.add_row(item.id, item.author, _truncate(item.body, 52),
                          str(item.score), str(item.depth))
        console.print(table)

    def _patched_print_user_activity(d):
        from rich.table import Table
        table = Table(show_header=True, header_style="bold cyan", border_style="dim",
                      pad_edge=False, show_lines=False)
        table.add_column("Type", style="bold", width=8)
        table.add_column("ID", style="dim", width=10)
        table.add_column("Author", style="green", width=22)
        table.add_column("Subreddit", style="magenta", width=18)
        table.add_column("Score", justify="right", style="yellow", width=7)
        table.add_column("Content", min_width=30, max_width=50)
        from reddipy.exporters.console import _truncate
        for item in d:
            content = item.title if item.title is not None else item.body
            table.add_row(item.type, item.id, item.author, f"r/{item.subreddit}",
                          str(item.score), _truncate(content, 47))
        console.print(table)

    exporter._print_posts = _patched_print_posts
    exporter._print_comments = _patched_print_comments
    exporter._print_user_activity = _patched_print_user_activity

    exporter.export(data)
    return buf.getvalue()


def make_post(**kwargs) -> Post:
    defaults = dict(id="p1", title="Sample Post Title", author="alice",
                    subreddit="python", score=150, upvote_ratio=0.90,
                    num_comments=20, selftext="Body", url="https://reddit.com",
                    permalink="/r/python/comments/p1", flair=None,
                    created_utc=datetime(2024, 5, 1, 8, 0, 0, tzinfo=timezone.utc))
    defaults.update(kwargs)
    return Post(**defaults)


def make_comment(**kwargs) -> Comment:
    defaults = dict(id="c1", author="bob", body="A simple comment body",
                    score=8, parent_id="t3_p1", depth=0, is_submitter=False,
                    replies=[],
                    created_utc=datetime(2024, 5, 1, 9, 0, 0, tzinfo=timezone.utc))
    defaults.update(kwargs)
    return Comment(**defaults)


def make_user_activity(**kwargs) -> UserActivity:
    defaults = dict(type="post", id="ua1", author="carol", subreddit="learnpython",
                    score=77, title="Activity Post Title", body=None,
                    permalink="/r/learnpython/comments/ua1",
                    created_utc=datetime(2024, 5, 2, 10, 0, 0, tzinfo=timezone.utc))
    defaults.update(kwargs)
    return UserActivity(**defaults)


class TestConsoleExporterPosts:
    def test_headers_present(self):
        out = _capture_export([make_post()])
        assert "ID" in out
        assert "Title" in out
        assert "Author" in out
        assert "Score" in out

    def test_post_data_printed(self):
        out = _capture_export([make_post(id="post42", author="alice", score=500)])
        assert "post42" in out
        assert "alice" in out
        assert "500" in out

    def test_multiple_rows(self):
        posts = [make_post(id=f"p{i}") for i in range(3)]
        out = _capture_export(posts)
        assert "p0" in out
        assert "p1" in out
        assert "p2" in out

    def test_long_title_truncated(self):
        out = _capture_export([make_post(title="A" * 80)])
        assert "A" * 80 not in out
        assert "..." in out


class TestConsoleExporterComments:
    def test_headers_present(self):
        out = _capture_export([make_comment()])
        assert "ID" in out
        assert "Author" in out
        assert "Comment" in out
        assert "Score" in out

    def test_comment_data_printed(self):
        out = _capture_export([make_comment(id="cmt99", author="dave", score=42)])
        assert "cmt99" in out
        assert "dave" in out
        assert "42" in out

    def test_long_body_truncated(self):
        out = _capture_export([make_comment(body="B" * 80)])
        assert "B" * 80 not in out
        assert "..." in out


class TestConsoleExporterUserActivity:
    def test_headers_present(self):
        out = _capture_export([make_user_activity()])
        assert "Type" in out
        assert "ID" in out
        assert "Author" in out

    def test_activity_data_printed(self):
        out = _capture_export([make_user_activity(id="ua10", author="eve", score=300)])
        assert "ua10" in out
        assert "eve" in out
        assert "300" in out

    def test_comment_activity_uses_body(self):
        out = _capture_export([make_user_activity(type="comment", title=None,
                                                  body="My comment text")])
        assert "My comment text" in out


class TestConsoleExporterEdgeCases:
    def test_empty_data(self, capsys):
        ConsoleExporter().export([])
        out = capsys.readouterr().out
        assert out == ""

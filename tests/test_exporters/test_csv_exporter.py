"""Tests for CSVExporter."""

import csv
import io
import os
import sys
from datetime import datetime, timezone

import pytest

from reddipy.models import Post, Comment, UserActivity
from reddipy.exporters.csv_exporter import CSVExporter


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def make_post(
    id="p1",
    title="A Test Post",
    author="alice",
    subreddit="python",
    score=200,
    upvote_ratio=0.92,
    num_comments=10,
    selftext="Hello world",
    url="https://reddit.com/r/python",
    permalink="/r/python/comments/p1",
    flair=None,
    created_utc=None,
) -> Post:
    if created_utc is None:
        created_utc = datetime(2024, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    return Post(
        id=id,
        title=title,
        author=author,
        subreddit=subreddit,
        score=score,
        upvote_ratio=upvote_ratio,
        num_comments=num_comments,
        created_utc=created_utc,
        selftext=selftext,
        url=url,
        permalink=permalink,
        flair=flair,
    )


def make_comment(
    id="c1",
    author="bob",
    body="A comment",
    score=5,
    parent_id="t3_p1",
    depth=0,
    is_submitter=False,
    replies=None,
    created_utc=None,
) -> Comment:
    if created_utc is None:
        created_utc = datetime(2024, 3, 1, 11, 0, 0, tzinfo=timezone.utc)
    if replies is None:
        replies = []
    return Comment(
        id=id,
        author=author,
        body=body,
        score=score,
        created_utc=created_utc,
        parent_id=parent_id,
        depth=depth,
        is_submitter=is_submitter,
        replies=replies,
    )


# ---------------------------------------------------------------------------
# Post export tests
# ---------------------------------------------------------------------------

class TestCSVExporterPosts:
    def test_export_posts_to_file_creates_file(self, tmp_path):
        posts = [make_post(id="p1"), make_post(id="p2")]
        exporter = CSVExporter()
        out = str(tmp_path / "posts.csv")
        exporter.export(posts, output_path=out)
        assert os.path.exists(out)

    def test_export_posts_headers_match_to_dict_keys(self, tmp_path):
        post = make_post()
        exporter = CSVExporter()
        out = str(tmp_path / "posts.csv")
        exporter.export([post], output_path=out)

        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

        expected = list(post.to_dict().keys())
        assert headers == expected

    def test_export_posts_data_values_correct(self, tmp_path):
        post = make_post(id="postX", title="Check Me", author="carol", score=999)
        exporter = CSVExporter()
        out = str(tmp_path / "data.csv")
        exporter.export([post], output_path=out)

        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["id"] == "postX"
        assert rows[0]["title"] == "Check Me"
        assert rows[0]["author"] == "carol"
        assert rows[0]["score"] == "999"

    def test_export_multiple_posts_creates_multiple_rows(self, tmp_path):
        posts = [make_post(id=f"p{i}") for i in range(5)]
        exporter = CSVExporter()
        out = str(tmp_path / "multi.csv")
        exporter.export(posts, output_path=out)

        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 5

    def test_export_posts_to_stdout(self, capsys):
        post = make_post(id="stdout_post", title="Console Title")
        exporter = CSVExporter()
        exporter.export([post])

        captured = capsys.readouterr()
        reader = csv.DictReader(io.StringIO(captured.out))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["id"] == "stdout_post"
        assert rows[0]["title"] == "Console Title"


# ---------------------------------------------------------------------------
# Comment flattening tests
# ---------------------------------------------------------------------------

class TestCSVExporterCommentFlattening:
    def test_flat_comment_no_replies_single_row(self, tmp_path):
        comment = make_comment(id="c1")
        exporter = CSVExporter()
        out = str(tmp_path / "flat.csv")
        exporter.export([comment], output_path=out)

        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["id"] == "c1"

    def test_nested_replies_flattened_to_three_rows(self, tmp_path):
        # grandchild -> child -> parent: all should appear as flat rows
        grandchild = make_comment(id="gc1", depth=2, parent_id="t1_c1")
        child = make_comment(id="c1", depth=1, parent_id="t3_p1", replies=[grandchild])
        parent = make_comment(id="p1", depth=0, replies=[child])
        exporter = CSVExporter()
        out = str(tmp_path / "nested.csv")
        exporter.export([parent], output_path=out)

        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
        ids = [r["id"] for r in rows]
        assert "p1" in ids
        assert "c1" in ids
        assert "gc1" in ids

    def test_flattened_rows_have_no_replies_column(self, tmp_path):
        child = make_comment(id="child", depth=1, parent_id="t1_parent")
        parent = make_comment(id="parent", replies=[child])
        exporter = CSVExporter()
        out = str(tmp_path / "no_replies_col.csv")
        exporter.export([parent], output_path=out)

        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = list(reader)

        assert "replies" not in headers
        for row in rows:
            assert "replies" not in row

    def test_flattened_rows_retain_depth_and_parent_id(self, tmp_path):
        child = make_comment(id="c2", depth=1, parent_id="t1_c1")
        parent = make_comment(id="c1", depth=0, parent_id="t3_p1", replies=[child])
        exporter = CSVExporter()
        out = str(tmp_path / "depth.csv")
        exporter.export([parent], output_path=out)

        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        parent_row = next(r for r in rows if r["id"] == "c1")
        child_row = next(r for r in rows if r["id"] == "c2")
        assert parent_row["depth"] == "0"
        assert child_row["depth"] == "1"
        assert child_row["parent_id"] == "t1_c1"

    def test_multiple_top_level_comments_each_with_replies(self, tmp_path):
        child_a = make_comment(id="ca", depth=1, parent_id="t1_a")
        child_b = make_comment(id="cb", depth=1, parent_id="t1_b")
        comment_a = make_comment(id="a", depth=0, replies=[child_a])
        comment_b = make_comment(id="b", depth=0, replies=[child_b])
        exporter = CSVExporter()
        out = str(tmp_path / "multi_top.csv")
        exporter.export([comment_a, comment_b], output_path=out)

        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 4
        ids = [r["id"] for r in rows]
        assert set(ids) == {"a", "ca", "b", "cb"}

    def test_comments_to_stdout(self, capsys):
        comment = make_comment(id="stdout_c", body="Hello from stdout")
        exporter = CSVExporter()
        exporter.export([comment])

        captured = capsys.readouterr()
        reader = csv.DictReader(io.StringIO(captured.out))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["id"] == "stdout_c"
        assert rows[0]["body"] == "Hello from stdout"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestCSVExporterEdgeCases:
    def test_empty_data_does_not_raise(self, tmp_path):
        exporter = CSVExporter()
        out = str(tmp_path / "empty.csv")
        exporter.export([], output_path=out)
        # File may not be created or may be empty; either is acceptable
        if os.path.exists(out):
            with open(out, encoding="utf-8") as f:
                content = f.read()
            assert content == ""

    def test_user_activity_export_to_file(self, tmp_path):
        activity = UserActivity(
            type="comment",
            id="ua1",
            author="dave",
            subreddit="askreddit",
            score=30,
            created_utc=datetime(2024, 4, 1, tzinfo=timezone.utc),
            title=None,
            body="My activity body",
            permalink="/r/askreddit/comments/ua1",
        )
        exporter = CSVExporter()
        out = str(tmp_path / "activity.csv")
        exporter.export([activity], output_path=out)

        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["type"] == "comment"
        assert rows[0]["author"] == "dave"

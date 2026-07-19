"""Tests for reddipy/utils.py"""
import re
import pytest
from reddipy.utils import parse_post_url, format_timestamp, generate_filename


class TestParsePostUrl:
    def test_full_url_with_trailing_slash(self):
        sub, post_id = parse_post_url(
            "https://www.reddit.com/r/claude/comments/1ukvj9j/some_title/"
        )
        assert sub == "claude"
        assert post_id == "1ukvj9j"

    def test_full_url_without_trailing_slash(self):
        sub, post_id = parse_post_url(
            "https://reddit.com/r/claude/comments/1ukvj9j/some_title"
        )
        assert sub == "claude"
        assert post_id == "1ukvj9j"

    def test_old_reddit_url(self):
        sub, post_id = parse_post_url(
            "https://old.reddit.com/r/claude/comments/1ukvj9j/"
        )
        assert sub == "claude"
        assert post_id == "1ukvj9j"

    def test_json_url(self):
        sub, post_id = parse_post_url(
            "https://www.reddit.com/r/claude/comments/1ukvj9j/some_title/.json"
        )
        assert sub == "claude"
        assert post_id == "1ukvj9j"

    def test_bare_permalink(self):
        sub, post_id = parse_post_url("/r/claude/comments/1ukvj9j/some_title/")
        assert sub == "claude"
        assert post_id == "1ukvj9j"

    def test_raises_on_missing_comments_segment(self):
        with pytest.raises(ValueError):
            parse_post_url("https://www.reddit.com/r/claude/")

    def test_raises_on_completely_wrong_format(self):
        with pytest.raises(ValueError):
            parse_post_url("https://example.com/not/a/reddit/url")

    def test_raises_on_empty_string(self):
        with pytest.raises(ValueError):
            parse_post_url("")


class TestFormatTimestamp:
    def test_known_timestamp(self):
        # 2024-01-15 14:30:00 UTC => Unix 1705329000
        result = format_timestamp(1705329000.0)
        assert result == "2024-01-15 14:30:00 UTC"

    def test_epoch_zero(self):
        result = format_timestamp(0.0)
        assert result == "1970-01-01 00:00:00 UTC"

    def test_returns_string(self):
        result = format_timestamp(1705329000.0)
        assert isinstance(result, str)


class TestGenerateFilename:
    def test_pattern_structure(self):
        result = generate_filename("search", "json")
        pattern = r"^reddipy_search_\d{8}_\d{6}\.json$"
        assert re.match(pattern, result), f"Filename '{result}' does not match expected pattern"

    def test_command_in_filename(self):
        result = generate_filename("posts", "csv")
        assert result.startswith("reddipy_posts_")
        assert result.endswith(".csv")

    def test_extension_applied(self):
        result = generate_filename("comments", "json")
        assert result.endswith(".json")

    def test_different_commands_differ(self):
        r1 = generate_filename("search", "json")
        r2 = generate_filename("posts", "json")
        # Commands differ so prefixes must differ
        assert r1.split("_")[1] == "search"
        assert r2.split("_")[1] == "posts"

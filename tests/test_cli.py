"""Tests for the CLI entry point."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from reddipy.cli import build_parser, export_data, main
from reddipy.exceptions import (
    NetworkError,
    SubredditNotFoundError,
)
from reddipy.exporters.console import ConsoleExporter


# ------------------------------------------------------------------
# Argument parsing tests
# ------------------------------------------------------------------


class TestArgParsing:
    """Verify subcommand arguments are parsed correctly."""

    def setup_method(self):
        self.parser = build_parser()

    def test_search_args_parsing(self):
        args = self.parser.parse_args(["search", "claude", "--limit", "50", "--sort", "top"])
        assert args.command == "search"
        assert args.query == "claude"
        assert args.limit == 50
        assert args.sort == "top"

    def test_post_args_parsing(self):
        url = "https://reddit.com/r/test/comments/abc/title/"
        args = self.parser.parse_args(["post", url])
        assert args.command == "post"
        assert args.url == url

    def test_subreddit_args_parsing(self):
        args = self.parser.parse_args(["subreddit", "python", "--sort", "hot", "--time", "week"])
        assert args.command == "subreddit"
        assert args.name == "python"
        assert args.sort == "hot"
        assert args.time == "week"

    def test_user_args_parsing(self):
        args = self.parser.parse_args(["user", "spez", "--type", "posts"])
        assert args.command == "user"
        assert args.username == "spez"
        assert args.type == "posts"

    def test_search_subreddit_flag(self):
        args = self.parser.parse_args(["search", "test", "-s", "python"])
        assert args.subreddit == "python"

    def test_common_flags(self):
        args = self.parser.parse_args([
            "search", "query",
            "--proxy", "http://proxy:8080",
            "--delay", "5.0",
            "--verbose",
            "--user-agent", "CustomBot/1.0",
            "--export", "json",
            "--output", "out.json",
        ])
        assert args.proxy == "http://proxy:8080"
        assert args.delay == 5.0
        assert args.verbose is True
        assert args.user_agent == "CustomBot/1.0"
        assert args.export == "json"
        assert args.output == "out.json"

    def test_default_values(self):
        # search defaults
        search_args = self.parser.parse_args(["search", "q"])
        assert search_args.limit == 25
        assert search_args.sort == "relevance"
        assert search_args.time == "all"
        assert search_args.export == "console"

        # subreddit defaults
        sub_args = self.parser.parse_args(["subreddit", "python"])
        assert sub_args.sort == "hot"

        # user defaults
        user_args = self.parser.parse_args(["user", "spez"])
        assert user_args.sort == "new"
        assert user_args.type == "all"


# ------------------------------------------------------------------
# main() flow tests
# ------------------------------------------------------------------


class TestMainFlow:
    """Verify main() dispatches correctly and handles errors."""

    def test_no_subcommand_exits(self):
        with patch("sys.argv", ["reddipy"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("reddipy.cli.SubredditScraper")
    @patch("reddipy.cli.RedditClient")
    def test_not_found_exits_3(self, mock_client_cls, mock_scraper_cls):
        mock_scraper = MagicMock()
        mock_scraper.scrape.side_effect = SubredditNotFoundError("r/nonexistent not found")
        mock_scraper_cls.return_value = mock_scraper

        with patch("sys.argv", ["reddipy", "subreddit", "nonexistent"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 3

    @patch("reddipy.cli.SearchScraper")
    @patch("reddipy.cli.RedditClient")
    def test_network_error_exits_2(self, mock_client_cls, mock_scraper_cls):
        mock_scraper = MagicMock()
        mock_scraper.scrape.side_effect = NetworkError("Connection failed")
        mock_scraper_cls.return_value = mock_scraper

        with patch("sys.argv", ["reddipy", "search", "test"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2

    @patch("reddipy.cli.generate_filename", return_value="reddipy_search_20240101_000000.json")
    @patch("reddipy.cli.SearchScraper")
    @patch("reddipy.cli.RedditClient")
    def test_auto_filename_when_no_output(self, mock_client_cls, mock_scraper_cls, mock_gen_fn):
        mock_scraper = MagicMock()
        mock_scraper.scrape.return_value = []
        mock_scraper_cls.return_value = mock_scraper

        with patch("sys.argv", ["reddipy", "search", "test", "--export", "json"]):
            main()

        mock_gen_fn.assert_called_once_with("search", "json")


# ------------------------------------------------------------------
# export_data tests
# ------------------------------------------------------------------


class TestExportData:
    """Verify export_data handles different data shapes."""

    def _make_args(self, **kwargs):
        defaults = {
            "command": "search",
            "export": "console",
            "output": None,
        }
        defaults.update(kwargs)
        import argparse
        return argparse.Namespace(**defaults)

    @patch("reddipy.cli.ConsoleExporter")
    def test_export_list_console(self, mock_exporter_cls):
        mock_exp = MagicMock(spec=ConsoleExporter)
        mock_exporter_cls.return_value = mock_exp
        args = self._make_args()

        export_data(["item1", "item2"], args)

        mock_exp.export.assert_called_once_with(["item1", "item2"], None)

    @patch("reddipy.cli.ConsoleExporter")
    def test_export_tuple_console(self, mock_exporter_cls):
        mock_exp = MagicMock(spec=ConsoleExporter)
        mock_exporter_cls.return_value = mock_exp
        args = self._make_args(command="post")

        mock_post = MagicMock()
        mock_comment = MagicMock()

        export_data((mock_post, [mock_comment]), args)

        # Should call export twice: once for post, once for comments
        assert mock_exp.export.call_count == 2

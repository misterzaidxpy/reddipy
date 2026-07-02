"""CLI entry point for RedMiner."""

import argparse
import json
import sys

from redminer.client import RedditClient
from redminer.exceptions import (
    NetworkError,
    PostNotFoundError,
    RateLimitError,
    RedMinerError,
    SubredditNotFoundError,
    UserNotFoundError,
)
from redminer.exporters import ConsoleExporter, CSVExporter, JSONExporter
from redminer.scrapers import PostScraper, SearchScraper, SubredditScraper, UserScraper
from redminer.utils import generate_filename


def _add_common_flags(parser: argparse.ArgumentParser) -> None:
    """Add flags shared by all subcommands."""
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--time", "-t", default="all",
                        choices=["day", "week", "month", "year", "all"])
    parser.add_argument("--export", default="console",
                        choices=["json", "csv", "console"])
    parser.add_argument("--output", "-o", default=None)
    parser.add_argument("--proxy", default=None)
    parser.add_argument("--proxy-file", default=None)
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--user-agent", default=None)
    parser.add_argument("--verbose", "-v", action="store_true", default=False)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="redminer",
        description="Scrape Reddit data from the command line.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # search
    search_parser = subparsers.add_parser("search", help="Search Reddit posts")
    search_parser.add_argument("query", type=str)
    search_parser.add_argument("--sort", default="relevance")
    search_parser.add_argument("--subreddit", "-s", default=None)
    _add_common_flags(search_parser)

    # post
    post_parser = subparsers.add_parser("post", help="Fetch a single post and its comments")
    post_parser.add_argument("url", type=str)
    post_parser.add_argument("--sort", default="best")
    _add_common_flags(post_parser)

    # subreddit
    sub_parser = subparsers.add_parser("subreddit", help="Fetch posts from a subreddit")
    sub_parser.add_argument("name", type=str)
    sub_parser.add_argument("--sort", default="hot")
    _add_common_flags(sub_parser)

    # user
    user_parser = subparsers.add_parser("user", help="Fetch user activity")
    user_parser.add_argument("username", type=str)
    user_parser.add_argument("--sort", default="new")
    user_parser.add_argument("--type", default="all",
                             choices=["posts", "comments", "all"])
    _add_common_flags(user_parser)

    return parser


def handle_search(client: RedditClient, args: argparse.Namespace) -> list:
    """Run a search scrape."""
    scraper = SearchScraper(client)
    return scraper.scrape(
        args.query,
        sort=args.sort,
        time_filter=args.time,
        limit=args.limit,
        subreddit=getattr(args, "subreddit", None),
    )


def handle_post(client: RedditClient, args: argparse.Namespace) -> tuple:
    """Run a post scrape."""
    scraper = PostScraper(client)
    post, comments = scraper.scrape(args.url)
    return (post, comments)


def handle_subreddit(client: RedditClient, args: argparse.Namespace) -> list:
    """Run a subreddit scrape."""
    scraper = SubredditScraper(client)
    return scraper.scrape(
        args.name,
        sort=args.sort,
        time_filter=args.time,
        limit=args.limit,
    )


def handle_user(client: RedditClient, args: argparse.Namespace) -> list:
    """Run a user scrape."""
    scraper = UserScraper(client)
    return scraper.scrape(
        args.username,
        limit=args.limit,
        sort=args.sort,
        activity_type=args.type,
    )


def export_data(data, args: argparse.Namespace) -> None:
    """Export scraped data using the selected exporter."""
    # Select exporter
    if args.export == "json":
        exporter = JSONExporter()
        ext = "json"
    elif args.export == "csv":
        exporter = CSVExporter()
        ext = "csv"
    else:
        exporter = ConsoleExporter()
        ext = None

    # Determine output path
    output_path = getattr(args, "output", None)
    if output_path is None and ext is not None:
        output_path = generate_filename(args.command, ext)

    # Handle post command specially (tuple of post, comments)
    if isinstance(data, tuple):
        post, comments = data
        if args.export == "console":
            print("=== Post ===")
            exporter.export([post])
            if comments:
                print("\n=== Comments ===")
                exporter.export(comments)
        elif args.export == "json":
            combined = {
                "post": post.to_dict(),
                "comments": [c.to_dict() for c in comments],
            }
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(combined, f, indent=2)
                print(f"Saved to {output_path}", file=sys.stderr)
            else:
                print(json.dumps(combined, indent=2))
        else:
            # CSV: export comments if available, otherwise the post
            if comments:
                exporter.export(comments, output_path)
            else:
                exporter.export([post], output_path)
            if output_path:
                print(f"Saved to {output_path}", file=sys.stderr)
    else:
        exporter.export(data, output_path)
        if output_path and ext:
            print(f"Saved to {output_path}", file=sys.stderr)


def main() -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not hasattr(args, "command") or args.command is None:
        parser.print_help()
        sys.exit(1)

    try:
        client = RedditClient(
            delay=args.delay,
            proxy=args.proxy,
            proxy_file=args.proxy_file,
            user_agent=args.user_agent,
            verbose=args.verbose,
        )

        if args.command == "search":
            data = handle_search(client, args)
        elif args.command == "post":
            data = handle_post(client, args)
        elif args.command == "subreddit":
            data = handle_subreddit(client, args)
        elif args.command == "user":
            data = handle_user(client, args)

        export_data(data, args)

    except (SubredditNotFoundError, PostNotFoundError, UserNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)
    except (NetworkError, RateLimitError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except RedMinerError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

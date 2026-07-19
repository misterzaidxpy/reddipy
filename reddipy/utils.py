"""Utility functions for reddipy."""
from datetime import datetime
from urllib.parse import urlparse


def parse_post_url(url: str) -> tuple[str, str]:
    """Parse a Reddit post URL and return (subreddit, post_id).

    Handles:
    - https://www.reddit.com/r/<sub>/comments/<id>/title/
    - https://reddit.com/r/<sub>/comments/<id>/title
    - https://old.reddit.com/r/<sub>/comments/<id>/
    - https://www.reddit.com/r/<sub>/comments/<id>/title/.json
    - Bare permalinks: /r/<sub>/comments/<id>/title/

    Raises ValueError for invalid or unrecognised URLs.
    """
    if not url:
        raise ValueError("URL must not be empty.")

    parsed = urlparse(url)
    path = parsed.path

    # Strip a trailing .json extension so it doesn't interfere with parsing
    if path.endswith(".json"):
        path = path[: -len(".json")]

    parts = [p for p in path.split("/") if p]  # drop empty segments

    # Expect at least: r, <subreddit>, comments, <post_id>
    try:
        comments_index = parts.index("comments")
    except ValueError:
        raise ValueError(
            f"Invalid Reddit post URL (no '/comments/' segment found): {url!r}"
        )

    # parts[comments_index - 2] should be 'r', parts[comments_index - 1] the subreddit
    if comments_index < 2 or parts[comments_index - 2] != "r":
        raise ValueError(
            f"Invalid Reddit post URL (missing '/r/<subreddit>/' before '/comments/'): {url!r}"
        )

    if comments_index + 1 >= len(parts):
        raise ValueError(
            f"Invalid Reddit post URL (no post ID after '/comments/'): {url!r}"
        )

    subreddit = parts[comments_index - 1]
    post_id = parts[comments_index + 1]
    return subreddit, post_id


def format_timestamp(utc: float) -> str:
    """Convert a Unix timestamp to a human-readable UTC string.

    Returns a string in the format: "2024-01-15 14:30:00 UTC"
    """
    from datetime import timezone
    return datetime.fromtimestamp(utc, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def generate_filename(command: str, ext: str) -> str:
    """Generate an auto filename for export output.

    Pattern: reddipy_{command}_{YYYYMMDD}_{HHMMSS}.{ext}
    Example: reddipy_search_20240115_143000.json
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"reddipy_{command}_{timestamp}.{ext}"

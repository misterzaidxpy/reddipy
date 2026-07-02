"""Data models for Reddit posts, comments, and user activity."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Self


@dataclass
class Post:
    """A Reddit post with only the fields we care about."""

    id: str
    title: str
    author: str
    subreddit: str
    score: int
    upvote_ratio: float
    num_comments: int
    created_utc: datetime
    selftext: str
    url: str
    permalink: str
    flair: str | None

    @classmethod
    def from_raw(cls, data: dict) -> Self:
        """Create a Post from a raw Reddit JSON data dict."""
        return cls(
            id=data["id"],
            title=data["title"],
            author=data["author"],
            subreddit=data["subreddit"],
            score=data["score"],
            upvote_ratio=data["upvote_ratio"],
            num_comments=data["num_comments"],
            created_utc=datetime.fromtimestamp(data["created_utc"], tz=timezone.utc),
            selftext=data["selftext"],
            url=data["url"],
            permalink=data["permalink"],
            flair=data.get("link_flair_text"),
        )

    def to_dict(self) -> dict:
        """Serialize to a plain dict with ISO-formatted datetime."""
        d = asdict(self)
        d["created_utc"] = self.created_utc.isoformat()
        return d


@dataclass
class Comment:
    """A Reddit comment, possibly with nested replies."""

    id: str
    author: str
    body: str
    score: int
    created_utc: datetime
    parent_id: str
    depth: int
    is_submitter: bool
    replies: list[Comment] = field(default_factory=list)

    @classmethod
    def from_raw(cls, data: dict) -> Self:
        """Create a Comment from a raw Reddit JSON data dict.

        Handles Reddit's nested reply structure: ``replies`` can be an
        empty string (no replies) or a listing dict.  Only ``t1`` kind
        children are processed; ``more`` stubs are skipped.
        """
        raw_replies = data.get("replies", "")
        parsed_replies: list[Comment] = []

        if isinstance(raw_replies, dict):
            for child in raw_replies["data"]["children"]:
                if child["kind"] == "t1":
                    parsed_replies.append(cls.from_raw(child["data"]))

        return cls(
            id=data["id"],
            author=data["author"],
            body=data["body"],
            score=data["score"],
            created_utc=datetime.fromtimestamp(data["created_utc"], tz=timezone.utc),
            parent_id=data["parent_id"],
            depth=data.get("depth", 0),
            is_submitter=data["is_submitter"],
            replies=parsed_replies,
        )

    def to_dict(self) -> dict:
        """Serialize to a plain dict with ISO-formatted datetime."""
        d = asdict(self)
        d["created_utc"] = self.created_utc.isoformat()
        # asdict already recursively converts nested dataclasses to dicts,
        # but we need to fix the datetime in each nested reply too.
        d["replies"] = [r.to_dict() for r in self.replies]
        return d


@dataclass
class UserActivity:
    """A single item from a user's history (either a post or a comment)."""

    type: str  # "post" or "comment"
    id: str
    author: str
    subreddit: str
    score: int
    created_utc: datetime
    title: str | None  # posts only
    body: str | None  # comments only
    permalink: str

    @classmethod
    def from_raw(cls, data: dict) -> Self:
        """Create a UserActivity from a raw Reddit JSON entry.

        ``data`` is the outer object containing ``kind`` and ``data`` keys.
        """
        kind = data["kind"]
        inner = data["data"]

        if kind == "t3":
            activity_type = "post"
            title = inner["title"]
            body = None
        else:
            activity_type = "comment"
            title = None
            body = inner["body"]

        return cls(
            type=activity_type,
            id=inner["id"],
            author=inner["author"],
            subreddit=inner["subreddit"],
            score=inner["score"],
            created_utc=datetime.fromtimestamp(inner["created_utc"], tz=timezone.utc),
            title=title,
            body=body,
            permalink=inner["permalink"],
        )

    def to_dict(self) -> dict:
        """Serialize to a plain dict with ISO-formatted datetime."""
        d = asdict(self)
        d["created_utc"] = self.created_utc.isoformat()
        return d

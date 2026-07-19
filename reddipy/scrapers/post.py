"""Post scraper for fetching a single Reddit post and its comments."""

from reddipy.models import Comment, Post
from reddipy.scrapers.base import BaseScraper
from reddipy.utils import parse_post_url


class PostScraper(BaseScraper):
    """Scrapes a single Reddit post with its comment tree."""

    def scrape(self, url: str) -> tuple[Post, list[Comment]]:
        """Fetch a post and its comments given a Reddit URL or permalink.

        Returns a tuple of (post, list_of_comments).
        """
        subreddit, post_id = parse_post_url(url)
        api_url = f"{self.client.BASE_URL}/r/{subreddit}/comments/{post_id}.json"

        response = self.client.fetch(api_url)

        # Reddit returns [post_listing, comments_listing]
        post_data = response[0]["data"]["children"][0]["data"]
        post = Post.from_raw(post_data)

        comments: list[Comment] = []
        for child in response[1]["data"]["children"]:
            if child["kind"] == "t1":
                comments.append(Comment.from_raw(child["data"]))

        return post, comments

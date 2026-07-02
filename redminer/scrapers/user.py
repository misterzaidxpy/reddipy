"""User scraper for fetching a Reddit user's activity history."""

from redminer.models import UserActivity
from redminer.scrapers.base import BaseScraper


class UserScraper(BaseScraper):
    """Scrapes a user's post and comment history."""

    def scrape(
        self,
        username: str,
        limit: int = 25,
        sort: str = "new",
        activity_type: str = "all",
    ) -> list[UserActivity]:
        """Fetch a user's activity history.

        Uses ``client.fetch()`` directly (not ``fetch_all``) because
        ``UserActivity.from_raw()`` needs the outer wrapper with the
        ``kind`` field, which ``fetch_all`` strips away.

        *activity_type* can be ``"all"``, ``"posts"``, or ``"comments"``
        to filter the returned items.
        """
        url = f"{self.client.BASE_URL}/user/{username}.json"
        params: dict = {"sort": sort, "limit": min(100, limit)}

        collected: list[dict] = []
        after: str | None = None

        while len(collected) < limit:
            page_params = {**params, "limit": min(100, limit - len(collected))}
            if after:
                page_params["after"] = after

            data = self.client.fetch(url, page_params)
            children = data.get("data", {}).get("children", [])

            for child in children:
                if len(collected) >= limit:
                    break
                collected.append(child)

            after = data.get("data", {}).get("after")
            if not after:
                break

        # Filter by activity type
        if activity_type == "posts":
            collected = [c for c in collected if c["kind"] == "t3"]
        elif activity_type == "comments":
            collected = [c for c in collected if c["kind"] == "t1"]

        return [UserActivity.from_raw(item) for item in collected]

"""Base scraper interface."""

from abc import ABC, abstractmethod

from redminer.client import RedditClient


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, client: RedditClient):
        self.client = client

    @abstractmethod
    def scrape(self, *args, **kwargs):
        pass

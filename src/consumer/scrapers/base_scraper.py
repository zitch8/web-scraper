from abc import ABC, abstractmethod
from typing import Tuple, Optional
from bs4 import BeautifulSoup
import logging

from config.logging_config import logging_config
logging_config(service_name='scraper')
logger = logging.getLogger(__name__)


class ScraperInterface(ABC):
    """Abstract base class for all scrapers"""

    def __init__(self, settings):
        """
        Initialize the scraper with configuration

        Args:
            settings: Scraper configuration object
        """
        self.settings = settings

    @abstractmethod
    def scrape(self, url: str) -> Tuple[Optional[BeautifulSoup], Optional[str]]:
        """
        Scrape a URL and return BeautifulSoup object

        Args:
            url: URL to scrape

        Returns:
            Tuple(BeautifulSoup object, error message)
        """
        pass

    @abstractmethod
    def close(self):
        """
        Close any resources held by the scraper
        """
        pass

    def validate_soup(self, soup: BeautifulSoup) -> bool:
        """
        Validate the scraped BeautifulSoup object

        Args:
            soup: BeautifulSoup object to validate

        Returns:
            bool: True if valid, False otherwise
        """

        required_elements = self.settings.scraper.selenium.get("required_elements", [])

        for element in required_elements:
            if element == "title":
                if not self._has_title(soup):
                    logger.warning("Validation failed: Missing title element")
                    return False
                
        return True
    
    def _has_title(self, soup: BeautifulSoup) -> bool:
        """Check if the soup has a title element"""
        title_sources = [
            soup.find('title'),
            soup.find('meta', property='og:title'),
            soup.find('meta', attrs={'name': 'title'}),
        ]

        return any(source and (source.get('content') if source.has_attr('content') else source.string) for source in title_sources)
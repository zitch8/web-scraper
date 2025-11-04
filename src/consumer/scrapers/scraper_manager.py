import logging
import time

from typing import Optional, Tuple

from .bs_scraper import BeautifulSoupScraper
from .selenium_scraper import SeleniumScraper
from .extractors import MetadataExtractor
from ...models.scraped_metadata import ScrapedMetadata

logger = logging.getLogger(__name__)

class ScraperManager:
    """
    Manages scraping strategy with fallback
    BS4 -> Selenium
    """

    def __init__(self, settings):
        """
        Initialize scraper manager
        
        Args:
            settings: ScraperConfig from settings
        """

        self.settings = settings

        self.bs_scraper = BeautifulSoupScraper(settings)
        self.selenium_scraper = SeleniumScraper(settings) if settings.selenium.enabled_fallback else None

        self.extractor = MetadataExtractor()

        logger.info("ScraperManager initialized")
        logger.info(f" - BeatifulSoup: enabled")
        logger.info(f" - Selenium: {'enabled' if self.selenium_scraper else 'disabled'} ")


    def scrape_article(self, url: str) -> Tuple[Optional[ScrapedMetadata], str, Optional[str]]:
        """
        Scrape article with fallback
        
        Args:
            url: URL to scrape

        Returns:
            Tuple of (ScrapedMetadata, method_used, error_message)
        """

        start_time = time.time()

        logger.info(f"Attempting to scrape: {url}")

        content, method, error = self._try_beautifulsoup(url)

        if not content and self.settings.selenium.enabled_fallback:
            logger.info(f"Triggering Selenium fallback for: {url}")
            content, method, error = self._try_selenium(url)
    
        processing_time = time.time() - start_time

        if content:
            logger.info(f"Successfully scraped {url} using {method} in {processing_time:.2f}s")
        else:
            logger.error(f"Failed to scrape {url}: {error}")

        return content, method, error
    
    def _try_beautifulsoup(self, url: str) -> Tuple[Optional[ScrapedMetadata], str, Optional[str]]:
        """
        Try scraping with BeautifulSoup
        
        Returns:
            Tuple of (ScrapedMetadata, 'beautifulsoup', error)
        """
        try:
            # Scrape with BS4
            soup, error = self.bs_scraper.scrape(url)
            
            if not soup:
                return None, 'beautifulsoup', error
            
            # Validate content
            if not self.bs_scraper.validate_soup(soup):
                error = "Content validation failed"
                logger.warning(f"BeautifulSoup validation failed for {url}")
                return None, 'beautifulsoup', error
            
            # Extract metadata
            content = self.extractor.extract(soup)
            
            # Validate extracted content
            if not content.is_valid():
                error = "Extracted content is invalid (no title found)"
                logger.warning(f"Extracted content validation failed for {url}")
                return None, 'beautifulsoup', error
            
            return content, 'beautifulsoup', None
            
        except Exception as e:
            error = f"BeautifulSoup error: {str(e)}"
            logger.error(f"{error}: {url}")
            return None, 'beautifulsoup', error
    
    def _try_selenium(self, url: str) -> Tuple[Optional[ScrapedMetadata], str, Optional[str]]:
        """
        Try scraping with Selenium
        
        Returns:
            Tuple of (ScrapedMetadata, 'selenium', error)
        """
        if not self.selenium_scraper:
            return None, 'selenium', "Selenium is disabled"
        
        try:
            # Scrape with Selenium
            soup, error = self.selenium_scraper.scrape(url)
            
            if not soup:
                return None, 'selenium', error
            
            # Extract metadata
            content = self.extractor.extract(soup)
            
            # Validate extracted content
            if not content.is_valid():
                error = "Selenium: Extracted content is invalid"
                logger.warning(f"Selenium extracted content validation failed for {url}")
                return None, 'selenium', error
            
            return content, 'selenium', None
            
        except Exception as e:
            error = f"Selenium error: {str(e)}"
            logger.error(f"{error}: {url}")
            return None, 'selenium', error
        
    def close(self):
        """Close all scrapers and release resources"""
        try:
            self.bs_scraper.close()
            if self.selenium_scraper:
                self.selenium_scraper.close()
            
            logger.info("ScraperManager closed")
        except Exception as e:
            logger.error(f"Error closing ScraperManager: {e}")

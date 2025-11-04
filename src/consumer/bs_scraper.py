import logging
import requests
import time

from bs4 import BeautifulSoup

from typing import Tuple, Optional

from src.consumer.base_scraper import ScraperInterface

logger = logging.getLogger(__name__)

class BeautifulSoupScraper(ScraperInterface):
    """Scraper using requests and BeautifulSoup for static content"""

    def __init__(self, settings):
        """
        Initialize the scraper with configuration

        Args:
            settings: Scraper configuration object
        """
        super().__init__(settings)
        self.session = requests.Session()
        
    def scrape(self, url: str)-> Tuple[Optional[BeautifulSoup], Optional[str]]:
        """Scrape a URL and return BeautifulSoup object"""

        for attempt in range(self.settings.request.max_retries):
            try:
                logger.info(f"Scraping with BeautifulSoup - URL: {url}, Attempt: {attempt + 1}/ {self.settings.request.max_retries}")

                response = self.session.get(
                    url,
                    timeout=self.settings.request.timeout
                )

                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                # Validate content type
                if not self.validate_soup(soup):
                    error_message = "Validation failed: Required elements not found, may need Selenium"
                    logger.warning(f"{error_message}: {url}")
                    return None, error_message
                
                logger.info(f"Successfully scraped URL with BeautifulSoup: {url}")
                return soup, None
            
            except requests.exceptions.Timeout:
                error_message = f"Timeout after {self.settings.request.timeout}s"
                logger.warning(f"{error_message} - Attempt {attempt + 1}")

                if attempt == self.settings.request.max_retries - 1:
                    # Exponential backoff

                    delay = self.settings.request.retry_delay ** attempt
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    return None, error_message
                
            except requests.exceptions.HTTPError as e:
                error_message = f"HTTP error: {e.response.status_code}: {str(e)}"
                logger.error(f"{error_message} - URL: {url}")
                
                return None, error_message
                
            except requests.exceptions.ConnectionError as e:
                error_message = f"Connection error: {str(e)}"
                logger.error(f"{error_message} - URL: {url}")

                if attempt < self.settings.request.max_retries - 1:
                    delay = self.settings.request.retry_delay ** attempt
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    return None, error_message
            
            except requests.exceptions.RequestException as e:
                error_message = f"Request exception: {str(e)}"
                logger.error(f"{error_message} - URL: {url}")
                
                return None, error_message
            
            except Exception as e:
                error_message = f"Unexpected error: {str(e)}"
                logger.error(f"{error_message} - URL: {url}")
                
                return None, error_message
    
        return None, "Max retries exceeded"
    def close(self):
        """Close the requests session"""
        try:
            self.session.close()
            logger.info("Beautiful Soup Requests session closed successfully")
        except Exception as e:
            logger.error(f"Error closing Beautiful Soup Requests session: {str(e)}")
import time
from typing import Optional, Tuple
import logging
from config.logging_config import logging_config

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

from webdriver_manager.chrome import ChromeDriverManager
from scrapers.base_scraper import ScraperInterface

logging_config(service_name='scraper')
logger = logging.getLogger(__name__)

class SeleniumScraper(ScraperInterface):
    """Scraper using selenium for JavaScript-rendered content"""

    def __init__(self, settings):
        super().__init__(settings)
        self.driver = None

        if self.settings.scraper.selenium.enabled_fallback:
            self._init_driver()
        
        else:
            logger.warning("Selenium is disabled in the configuration.")

    def _init_driver(self):
        try:
            chrome_options = self.settings.scraper.selenium.get_chrome_options()
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            self.driver.set_page_load_timeout(self.settings.scraper.selenium.timeout)
            self.driver.implicitly_wait(self.settings.scraper.selenium.implicit_wait)

            logger.info("Selenium WebDriver initialized successfully.")
        
        except Exception as e:
            logger.error(f"Failed to initialize Selenium WebDriver: {str(e)}")

    def scrape(self, url: str) -> Tuple[Optional[BeautifulSoup], Optional[str]]:
        """
        Scrape URL using Selenium

        Args:
            url: URL to scrape
        
        Returns:
            Tuple(BeautifulSoup object, error message)
        """

        if not self.driver:
            return None, "Selenium WebDriver is not initialized."
        
        try:
            logger.info(f"Scraping with Selenium - URL: {url}")

            self.driver.get(url)

            WebDriverWait(self.driver, self.config.scraper.selenium.page_load_timeout).until(
                EC.presence_of_element_located(By.TAG_NAME, "body")
            )

            html = self.driver.page_source

            soup = BeautifulSoup(html, 'html.parser')

            if not self.validate_soup(soup):
                error_message = "Content validation failed even with Selenium."
                logger.warning(f"{error_message} - URL: {url}")
                return soup, error_message
            
            logger.info(f"Successfully scraped URL with Selenium: {url}")
            return soup, None
        
        except TimeoutException:
            error_message = f"Selenium timeout after {self.settings.scraper.selenium.timeout}s"
            logger.warning(f"{error_message} - URL: {url}")
            return None, error_message
        
        except WebDriverException as e:
            error_message = f"Selenium WebDriver error: {str(e)}"
            logger.error(f"{error_message} - URL: {url}")
            return None, error_message
        
        except Exception as e:
            error_message = f"Unexpected error during Selenium scraping: {str(e)}"
            logger.error(f"{error_message} - URL: {url}")
            return None, error_message

    def close(self):
        """Close the WebDriver"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("Selenium WebDriver closed successfully.")
        except Exception as e:
            logger.error(f"Error closing Selenium WebDriver: {str(e)}")
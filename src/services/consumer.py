import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from src.publisher.redis_queue import RedisManager
from src.db.mongoDB import MongoDB
from src.consumer.scraper_manager import ScraperManager

from src.models.article_metadata import ArticleMetadata
from src.models.article import Article

logger = logging.getLogger(__name__)

class Consumer:
    """
    Service Consumer class for consuming articles from Redis then process them
    
    """
    def __init__(self, queue_manager: RedisManager, db: MongoDB, 
                 scraper_manager: ScraperManager, settings):
        
        """
        Initialize consumer service

        Args:
            queue_manager: RedisManager instance
            db: MongoDB instance
            scraper_manager: ScraperManager instance
            settings: ConsumerConfig from settings
        """

        self.queue_manager = queue_manager
        self.db = db
        self.scraper_manager = scraper_manager
        self.settings = settings

        self.stats = {
            'total_processed': 0,
            'success': 0,
            'failed': 0,
            'by_priority': {'high': 0, 'medium': 0, 'low': 0},
            'by_method': {'beautifulsoup': 0, 'selenium': 0, 'failed': 0},
            'start_time': None,
            'last_processed': None
        }

        self.running = False

    def consume_and_process(self) -> bool:
        """
        Consume one article from queue then process

        Returns:
            True if article was process, else False if empty
        """

        article_data = self.queue_manager.pop(timeout=0)

        if not article_data:
            return False
        

        self._process_article(article_data)

        return True
    

    def _process_article(self, article_data):
        """
        Process single article: scrape, extract, store

        Args:
            article_data: ArticleMetadata dictionary
        """
        start_time = time.time()
        
        try:
            metadata = ArticleMetadata(**article_data)
            article = Article.from_metadata(metadata)     
            existing = self.db.find_by_url_hash(article.technical_metadata.url_hash)
            
            if existing and existing.technical_metadata.status == "success":
                logger.info(f"Article already exists, skipping: {article.url}")

            else:

                logger.info(f"Processing article {article.id}: {article.url}")

                content, method, error = self.scraper_manager.scrape_article(article.url)

                processing_time = time.time() - start_time

                if content:
                    article.mark_success(content, method, processing_time)
                    self.stats['success'] += 1
                    self.stats['by_method'][method] += 1

                else:
                    article.mark_failed(error or 'Unknown error', method)
                    self.stats['failed'] += 1
                    self.stats['by_method']['failed'] += 1
                
                if self.db.save(article):
                    logger.info(f"Stored article {article.id} (status: {article.technical_metadata.status})")
                else:
                    logger.error(f"Failed to store article {article.id}")

                
            self.stats['total_processed'] += 1
            self.stats['by_priority'][article.priority.lower()] += 1
            self.stats['last_processed'] = datetime.now().isoformat()

            self._log_progress()

        except Exception as e:
            logger.exception(f"Error processing article: {e}")
            self.stats['failed'] += 1

    
    def run(self, max_articles: Optional[int] = None):
        """
        Main consuer loop

        Args:
            max_articles: Maximum articles to process (None = Unli)
        """

        max_articles = max_articles or self.settings.max_articles

        self.running = True
        self.stats['start_time'] = datetime.now().isoformat()

        logger.info("=" * 50)
        logger.info("Consumer starting...")
        logger.info("=" * 50)
        logger.info(f"Max articles: {max_articles if max_articles else 'unlimited'}")
        logger.info(f"Batch size: {self.settings.batch_size}")
        logger.info(f"=" * 50)


        try:
            while self.running:
                if max_articles and self.stats['total_processed'] >= max_articles:
                    logger.info(f"Reached max articles limit: {max_articles}")
                    break

                processed = False

                for _ in range(self.settings.batch_size):
                    if self.consume_and_process():
                        processed = True
                    
                    else:
                        break

                if not processed:
                    logger.debug(f"No articles in queue. Waiting {self.settings.poll_interval}s...")
                    time.sleep(self.settings.poll_interval)

        except KeyboardInterrupt:
            logger.info("\nConsumer stopped by user")

        finally:
            self._shutdown()

    def _log_progress(self):
        """Log current progress"""
        success_rate = 0

        if self.stats['total_processed'] > 0:
            success_rate = self.stats['success'] / self.stats['total_processed'] * 100
        
        logger.info("-" * 50)
        logger.info(f"Progress: {self.stats['total_processed']} articles processed")
        logger.info(f"  Success: {self.stats['success']} ({success_rate:.1f}%)")
        logger.info(f"  Failed: {self.stats['failed']}")
        logger.info(f"  By method: BS4={self.stats['by_method']['beautifulsoup']}, "
                    f"Selenium={self.stats['by_method']['selenium']}")
        logger.info("-" * 50)

    def _shutdown(self):
        """Cleanup and show final stats"""
        self.running = False

        logger.info("=" * 50)
        logger.info("Consumer Shutting Down")
        logger.info("=" * 50)

        self._print_final_statistics()

        try:
            self.scraper_manager.close()
            logger.info("Scraper manager closed")
        except Exception as e:
            logger.error(f"Error closing scraper manager: {e}")

    
    def _print_final_statistics(self):
        """Print comprehensive final statistics"""

        logger.info("FINAL STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Total processed: {self.stats['total_processed']}")
        logger.info(f"Successful: {self.stats['success']}")
        logger.info(f"Failed: {self.stats['failed']}")
        
        if self.stats['total_processed'] > 0:
            success_rate = self.stats['success'] / self.stats['total_processed'] * 100
            logger.info(f"Success rate:         {success_rate:.2f}%")
        
        logger.info("-" * 50)
        logger.info("By Priority:")
        for priority, count in self.stats['by_priority'].items():
            logger.info(f"  {priority.capitalize()}: {count}")
        
        logger.info("-" * 50)
        logger.info("By Scraping Method:")
        logger.info(f"  BeautifulSoup: {self.stats['by_method']['beautifulsoup']}")
        logger.info(f"  Selenium: {self.stats['by_method']['selenium']}")
        logger.info(f"  Failed: {self.stats['by_method']['failed']}")
        
        logger.info("-" * 50)
        
        # Database statistics
        db_stats = self.db.get_statistics()
        logger.info("Database Statistics:")
        logger.info(f"  Total in DB: {db_stats.get('total', 0)}")
        logger.info(f"  Success in DB: {db_stats.get('success', 0)}")
        logger.info(f"  Failed in DB: {db_stats.get('failed', 0)}")
        logger.info(f"  Success rate: {db_stats.get('success_rate', '0%')}")
        
        logger.info("=" * 50)

    def get_statistics(self) -> Dict[str, Any]:
        """Geut current statistics"""

        return self.stats.copy()

    def stop(self):
        """Stop the consumer"""
        logger.info("Stop signal received")
        self.running = False
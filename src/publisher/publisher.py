import logging
from config.logging_config import logging_config

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from models.article_metadata import ArticleMetadata
from publisher.redis_queue import RedisManager

# Logging configuration
logging_config(service_name="publisher")
logger = logging.getLogger(__name__)
    
class Publisher:
    """
    Service Publisher clas for articles to Redis queue
    Handles JSON
    """

    def __init__(self, queue_manager: RedisManager, settings):
        """
        Initialize publisher service
        """

        self.queue_manager = queue_manager
        self.settings = settings
        self.stats = {
            'total_loaded' : 0,
            'total_published' : 0,
            'total_failed' : 0,
            'by_priority' : {'high' : 0, 'medium' : 0, 'low' : 0},
            'start_time' : None,
            'end_time' : None
        }

    def load_articles_from_json(self, file: str) -> List[ArticleMetadata]:
        """
        Load articles from JSON file
        
        Args:
            file_path: Path to JSON file

        Returns:
            List of valid ArticleMetadata objects
        """

        articles = []

        try:
            file_path = Path(file)

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            articles_data = data.get('articles', [])

            for article_data in articles_data:
                try:
                    article = ArticleMetadata(**article_data)

                    if article.validate():
                        articles.append(article)
                    else:
                        logger.warning(f"Invalid article data: {article_data}")

                except TypeError as e:
                    logger.warning(f"Failed to prase article: {e}")
                    continue

                except ValueError as e:
                    logger.warning(f"Failed to parse article: {e}")
                    continue
            
            self.stats['total_loaded'] = len(articles)
            logger.info(f"Loaded {len(articles)} valid articles from {file_path}")

            return articles
    
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            raise
            
        except Exception as e:
            logger.error(f"Error loading articles: {e}")
            raise

    def publish_single(self, article: ArticleMetadata) -> bool:
        """
        Publish single article

        Args:
            article: ArticleMetadata object
        
        Returns:
            True if successful
        """

        success = self.queue_manager.push(article)
        if success:
            logger.info(f"Published article {article.id} (priority: {article.priority})")
            return True

        else:
            logger.error(f"Failed to publish article {article.id}")
            return False
        

    def publish_batch(self, articles: List[ArticleMetadata]) -> Dict[str, Any]:
        """
        Publish multiple articles in batches

        Returns:
            Dict of statistics
        """

        self.stats['start_time'] = datetime.now().isoformat()

        logger.info(f"Starting to publish {len(articles)} articles...")

        batch_size = self.config.batch_size

        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            batch_stats = self.queue_manager.push_batch(batch)

            self.stats['total_published'] += batch_stats['success']
            self.stats['total_failed'] += batch_stats['failed']


            for priority, count in batch_stats['by_priority'].items():
                self.stats['by_priority'][priority] += count

            
            logger.info(f"Processed batch {i//batch_size + 1}: {batch_stats['success']}/{len(batch)} successful")

        self.stats['end_time'] = datetime.now().isoformat()

        return self.stats


    def publish_from_file(self, file_path: str = None) -> Dict[str, Any]:
        """
        Complete flow: load from file -> publish

        Args:
            file_path: Path to articles JSON (use config default if None)
        
        Returns:
            Dict of statistics
        """
        file_path = file_path or self.config.input_file

        # Clear queues on start if configured
        if self.config.clear_queues_on_start:
            logger.info("Clearing existing queues...")
            self.queue_manager.clear_all_queues()

        articles = self.load_articles_from_json(file_path)

        if not articles:
            logger.warning("No valid articles to publish")
            return self.stats

        publish_stats = self.publish_batch(articles)

        return publish_stats


    def _print_statistics(self):
        """Print publishing statistics"""
        logger.info("=" * 50)
        logger.info("PUBLISHING STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Total articles loaded: {self.stats['total_loaded']}")
        logger.info(f"Successfully published: {self.stats['total_published']}")
        logger.info(f"Failed: {self.stats['total_failed']}")
        logger.info("-" * 50)
        logger.info("By Priority:")
        for priority, count in self.stats['by_priority'].items():
            logger.info(f"  {priority.capitalize()}: {count}")
        logger.info("-" * 50)
        
        # Show current queue lengths
        queue_lengths = self.queue_manager.get_all_queue_lengths()
        logger.info("Current Queue Lengths:")
        for priority, length in queue_lengths.items():
            logger.info(f"  {priority.capitalize()}: {length}")
        logger.info("=" * 50)

    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics"""
        return self.stats.copy()
    
    def reset_statistics(self):
        """Reset statistics counters"""
        self.stats = {
            'total_loaded': 0,
            'total_published': 0,
            'total_failed': 0,
            'by_priority': {'high': 0, 'medium': 0, 'low': 0},
            'start_time': None,
            'end_time': None
        }
import json
import logging
from typing import List, Dict, Optional

from config.logging_config import logging_config

from redis import Redis, RedisError
from dataclasses import asdict

from models.article_metadata import ArticleMetadata

logging_config(service_name="publisher")
logger = logging.getLogger(__name__)

class RedisManager:
    """
    Manages Redis queue for article publishing and consumption
    """

    def __init__(self, settings):
        """
        Initialize Redis queue

        Args:
            config: RedisConfig object from settings
        """

        self.settings = settings
        self.client = None
        self._connect()

    def _connect(self):
        """Establish Redis connection"""

        try:
            self.client = Redis(**self.settings.to_client_kwargs())
            self.client.ping()
            logger.info(f"Connected to Redis at {self.settings.host}:{self.settings.port}")

        except RedisError as e:
            logger.error(f"Failed to connec to Redis: {e}")
            raise

    def push(self, article_metadata: ArticleMetadata) -> bool:
        """
        Push article to appropriate priority queue

        Args:
            article_metadata: ArticleMetadata object
        """

        try:
            queue_name = self.config.get_queue_name(article_metadata.priority)
            article_json = json.dumps(asdict(article_metadata))

            # FiFo method
            self.client.lpush(queue_name, article_json)
            logger.debug(f"Pushed article {article_metadata.id} to {queue_name}")
            return True
        
        except RedisError as e:
            logger.error(f"Failed to push article {article_metadata.id}: {e}")
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error pushing article {article_metadata}: e")
            return False
        
    def push_batch(self, articles: List[ArticleMetadata]) -> Dict[str, int]:

        """
        Pushed multiple articles to queues

        Args:
            articles: List of ArticleMetadata objects
        
        Returns:
            Dict with stats
        """

        stats = {
            'total' : len(articles),
            'success': 0,
            'failed' : 0,
            'by_priority': {'high': 0, 'medium': 0, 'low': 0}
        }

        for article in articles:
            if self.push(article):
                stats['success'] += 1
                priority = article.priority.lower()
                stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
            else:
                stats['failed'] += 1

        return stats
    
    def pop(self, priority: Optional[str] = None, timeout: int = 0) -> Optional[Dict]:
        """
        Pop article from queue ()
        """

        try:
            queue_name = self.settings.get_queue_name(priority)
            result = self._pop_from_queue(queue_name, timeout)

            if result:
                article = json.loads(result)
                logger.debug(f"Popped article {article.get('id')} from queue")
                return article
        
            return None

        except RedisError as e:
            logger.error(f"Error popping from queue: {e}")
            return None
        
        except json.JSONDecodeError as e:
            logger.error(f"Error popping from queue: {e}")
            return None
                
    def _pop_from_queue(self, queue_name: str, timeout: int) -> Optional[str]:
        """Pop from specific queue"""

        try:
            if timeout > 0:
                result = self.client.brpop(queue_name, timeout=timeout)
                return result[1] if result else None
            
            else:
                return self.client.rpop(queue_name)
            
        except RedisError as e:
            logger.error(f"Error popping from {queue_name}: {e}")
            return None
        
    def get_queue_length(self, priority: str) -> int:

        """
        Get length of specific queue

        Args:
            priority: Queue priority ('high', 'medium', 'low')

        Returns:
            queuel length or error -1
        """

        try:
            queue_name = self.config.get_queue_name(priority)
            return self.client.llen(queue_name)
        except RedisError as e:
            logger.error(f"Failed to get queue length: {e}")
            return -1
        
    
    def get_all_queue_lengths(self) -> Dict[str, int]:
        """ Get lenghts of all queues"""

        return {
            'high' : self.get_queue_length('high'),
            'medium' : self.get_queue_length('medium'),
            'low': self.get_queue_length('low')
        }
    
    def clear_queue(self, priority: str) -> bool:
        """
        Clear specific queue

        Args:
            priority: Queue priority to clear

        Returns:
            True if successful
        """

        try:
            queue_name = self.config.get_queue_name(priority)
            self.client.delete(queue_name)
            logger.info(f"Cleared queue: {queue_name}")
            return True
        except RedisError as e:
            logger.error(f"Failed to clear queue {priority}: {e}")
            return False
        
    def clear_all_queues(self) -> bool:
        """Clear all article queues"""
        try:
            self.client.delete(
                self.config.queue_high,
                self.config.queue_medium,
                self.config.queue_low
            )
            logger.info("Cleared all queues")
            return True
        except RedisError as e:
            logger.error(f"Failed to clear queues: {e}")
            return False

    def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            return self.client.ping()
        except RedisError:
            return False
    
    def close(self):
        """Close Redis connection"""
        try:
            if self.client:
                self.client.close()
                logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
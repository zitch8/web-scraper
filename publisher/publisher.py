import logging
import json

from redis import Redis, RedisError

from typing import List, Dict
from dataclasses import asdict

from models.article import Article

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
    
class Publisher:
    """Publisher clas for articles to Redis"""

    PRIORITY_DICT = {
        'high': 'articles:queue:high',
        'medium': 'articles:queue:medium',
        'low': 'articles:queue:low',
    }

    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379, redis_db: int = 0):
        """Initialize Redis client"""
        try:
            self.redis_client = Redis(
                host = redis_host,
                port = redis_port,
                db = redis_db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            logger.info(f"Connected to Redis successfully at HOST: {redis_host}:{redis_port}, DB: {redis_db}")  
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def load_articles(self, json_file: str) -> List[Article]:
        """Load articles from a JSON file"""
        try:
            with open(json_file, 'r') as file:
                data = json.load(file)
            
            articles = []
            for article_data in data:
                article = Article(**article_data)
                if article.validate():
                    articles.append(article)
                else:
                    logger.warning(f"Invalid article data: {article_data}")

            logger.info(f"Loaded {len(articles)} valid articles from {json_file}")
            return articles
        except FileNotFoundError:
            logger.error(f"File not found: {json_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from file {json_file}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading articles from {json_file}: {e}")
            raise

    def publish_article(self, article: Article) -> bool:
        """Publish single article to appropriate priority queue in Redis"""
        try:
            queue_name = self.PRIORITY_DICT.get(
                article.priority.value
            )

            article_json = json.dumps(asdict(article))
            self.redis_client.lpush(queue_name, article_json)

            logger.info(f"Published article ID: {article.id} to QUEUE: {queue_name}")
            return True
        except RedisError as e:
            logger.error(f"Failed to publish article ID: {article.id} to Redis: {e}")
            return False
        
    def publish_batch(self, articles: List[Article]) -> Dict[str, int]:
        """Publish batch of articles to Redis and return summary"""
        summary = {
            'total': len(articles),
            'successful': 0,
            'failed': 0,
            'by_priority': {
                'high': 0,
                'medium': 0,
                'low': 0
            }
        }

        for article in articles:
            if self.publish_article(article):
                summary['successful'] += 1
                summary['by_priority'][article.priority.lower()] += 1
            else:
                summary['failed'] += 1

        logger.info(f"Batch publish summary: {summary}")
        return summary
    
    def get_queue_stats(self)->Dict[str, int]:
        """Get current queue lengths"""
        stats = {}
        for priority, queue_name in self.PRIORITY_DICT.items():
            try:
                length = self.redis_client.llen(queue_name)
                stats[priority] = length
            except RedisError as e:
                logger.error(f"Failed to get length of queue {queue_name}: {e}")
                stats[priority] = -1  # Indicate error

        return stats
    
    def _close(self):
        """Close Redis connection"""
        try:
            self.redis_client.close()
            logger.info("Closed Redis connection successfully")
        except RedisError as e:
            logger.error(f"Failed to close Redis connection: {e}")
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
    
    def __enter__(self):
        return self

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
    # TODO: Implement queue monitoring and retry logic

    

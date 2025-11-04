import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


import logging

from config.logging_config import logging_config
from config.settings import settings

from src.consumer.consumer import Consumer
from src.consumer.scrapers.scraper_manager import ScraperManager
from src.publisher.redis_queue import RedisManager
from src.db.mongoDB import MongoDB

def main():
    """Consumer Service Main Execution"""

    logging_config(service_name="consumer")
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("Consumer starting")
    logger.info("=" * 50)

    try:
        is_valid, errors = settings.validate()
        if not is_valid:
            logger.error("Configuration validation failed: ")
            for error in errors:
                logger.error(f" - {error}")

            return 1
        
        logger.info("Configuration valid")

        logger.info("Initializing Redis connection...")
        queue_manager = RedisManager(settings.redis)

        if not queue_manager.health_check():
            logger.error("Redis health check failed")
            return 1
        
        logger.info("Redis connected")

        queue_lengths = queue_manager.get_all_queue_lengths()
        logger.info(f"Queue status: High={queue_lengths['high']}, "
                    f"Medium = {queue_lengths['medium']}, Low ={queue_lengths['low']}")
        
        logger.info("Initializing MongoDB connection...")

        db = MongoDB(settings.mongodb)

        if not db.health_check():
            logger.info("MongoDB health check failed")
            queue_manager.close()
            return 1
        
        logger.info("MongoDB connected")

        db_stats = db.get_statistics()
        logger.info(f"Database status: {db_stats.get('total', 0)} articles, "
                   f"Success rate: {db_stats.get('success_rate', '0%')}")
        
        logger.info("Initializing scraper manager...")
        scraper_manager = ScraperManager(settings.scraper)
        logger.info("Scraper manager ready")

        logger.info("Initializing consumer service...")
        consumer_service = Consumer(
            queue_manager,
            db,
            scraper_manager,
            settings.consumer
        )
        logger.info("Consumer service ready")

        max_articles = settings.consumer.max_articles


        logger.info("=" * 50)
        logger.info("Starting to consume articles...")
        logger.info("Ctrl + C to stop")
        logger.info("=" * 50)

        try:
            consumer_service.run(max_articles=max_articles)
                       
        except KeyboardInterrupt:
            logger.info("Cosumer service interrupted")
        finally:
            logger.info("Closing connections...")
            try:
                consumer_service.stop()
            except Exception:
                logger.exception("Error while stopping consumer service")

            queue_manager.close()
            db.close()

            logger.info("Shutdow complete")

        return 0
    
    except KeyboardInterrupt:
        logger.info ("\nConsumer stopped by user")
        return 0
    
    except Exception as e:
        logger.exception(f"Consumer failed with error {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())



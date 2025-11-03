import logging
import sys

from src.publisher.redis_queue import RedisManager
from src.publisher.publisher import Publisher

from config.settings import settings
from config.logging_config import logging_config

def main():
    """Main execution"""

    logging_config(service_name="publisher")
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("Publisher starting")
    logger.info("=" * 50)

    try:

        # Validate configuration
        is_valid, errors = settings.validate()
        if not is_valid:
            logger.error("Configuration validation failed: ")
            for error in errors:
                logger.error(f" - {error}")
            return 1
        
        # Init Redis queue
        logger.info("Initializing Redis connection...")
        queue_manager = RedisManager(settings.redis)

        if not queue_manager.health_check():
            logger.error("Redis health check failed")
            return 1
        
        logger.info("Initializing Publisher Service...")
        publisher = Publisher(queue_manager, settings.publisher)

        input_file = settings.publisher.input_file
        logger.info(f"Input file: {input_file}")

        # Publish articles
        logger.info("Starting to publish articles...")
        stats = publisher.publish_from_file(input_file)

        # Show stats
        logger.info("=" * 50)
        if stats['total_failed'] == 0:
            logger.info("Publishing completed successfully!")
            return_code = 0

        else:
            logging.warning(f"Publishing compelted with {stats['total_failed']} failures")
            return_code = 1

        logger.info("=" * 50)

        queue_manager.close()

        return return_code
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1

    except KeyboardInterrupt:
        logger.info("\nPublisher stopped by user")
        return 0
    except Exception as e:
        logger.exception(f"Publisher failed with error: {e}")
        return 1
    
if __name__ == "__main__":
    sys.exit(main())



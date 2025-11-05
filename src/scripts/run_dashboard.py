import sys
import logging
from src.config.logging_config import logging_config

from src.config.settings import settings
from src.publisher.redis_queue import RedisManager
from src.db.mongoDB import MongoDB
from src.api.dashboard import DashboardAPI

def main():
    logging_config(service_name="dashboard")
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("Dashboard API Starting")
    logger.info("=" * 50)

    try:
        # Validate configuration
        is_valid, errors = settings.validate()
        if not is_valid:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return 1
        
        # Initialize Redis queue manager
        logger.info("Connecting to Redis...")
        queue_manager = RedisManager(settings.redis)
        
        if not queue_manager.health_check():
            logger.error("Redis health check failed")
            return 1
        logger.info("Redis connected")
        
        # Initialize MongoDB storage
        logger.info("Connecting to MongoDB...")
        db = MongoDB(settings.mongodb)
        
        if not db.health_check():
            logger.error("MongoDB health check failed")
            queue_manager.close()
            return 1
        logger.info("MongoDB connected")
        
        # Initialize Dashboard API
        logger.info("Initializing Dashboard API...")
        dashboard = DashboardAPI(queue_manager, db, settings.dashboard)
        logger.info("Dashboard API ready")

        logger.info("=" * 50)
        logger.info(f"Dashboard API running on http://{settings.dashboard.host}:{settings.dashboard.port}")
        logger.info(f"CORS enabled: {settings.dashboard.enable_cors}")
        logger.info("=" * 50)
        logger.info("Available endpoints:")
        logger.info("  GET  /health          - Health check")
        logger.info("  GET  /articles/<id>   - Get single article")
        logger.info("  GET  /articles/failed - Get failed articles")
        logger.info("  GET  /queue/stats     - Queue statistics")
        logger.info("  POST /queue/clear     - Clear all queues")
        logger.info("=" * 50)

        dashboard.run()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nDashboard stopped by user")
        return 0
    except Exception as e:
        logger.exception(f"Dashboard failed with error: {e}")
        return 1
    
if __name__ == "__main__":
    sys.exit(main())
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

from src.publisher.redis_queue import RedisManager
from src.db.mongoDB import MongoDB

logger = logging.getLogger(__name__)

class DashboardAPI:
    def __init__(self, queue_manager: RedisManager, 
                 db: MongoDB,
                 settings):
        """
        Initialize Dashboard API
        
        Args:
            queue_manager: RedisManager instance
            db: MongoDB instance
            settings: DashboardConfig from settings
        """
        self.queue_manager = queue_manager
        self.db = db
        self.settings = settings
        
        # Initialize Flask app
        self.app = Flask(__name__)

        if settings.enable_cors:
            CORS(self.app, origins=settings.cors_origins)

        self._register_routes()
        logger.info("Dashboard API Initialized")

    def _register_routes(self):
        """Register all API routes"""

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return self._health_check()
        
        @self.app.route('/queue/stats', methods=['GET'])
        def queue_stats():
            """Get queue statistics"""
            return self._get_queue_stats()
        
        @self.app.route('/queue/clear', methods=['POST'])
        def clear_queues():
            """Clear all queues"""
            return self._clear_queues()
        
        @self.app.route('/articles/failed', methods=['GET'])
        def get_failed_articles():
            """Get all failed articles"""
            return self._get_failed_articles()
        
        @self.app.route('/articles/<article_id>', methods=['GET'])
        def get_article(article_id):
            """Get single article by ID"""
            return self._get_article(article_id)
        
        # TODO: Add the metrics
        
    def _health_check(self):
        try:
            redis_ok = self.queue_manager.health_check()
            mongo_ok = self.db.health_check()
            
            status = 'healthy' if (redis_ok and mongo_ok) else 'unhealthy'
            status_code = 200 if status == 'healthy' else 503
            
            return jsonify({
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'services': {
                    'redis': 'up' if redis_ok else 'down',
                    'mongodb': 'up' if mongo_ok else 'down'
                }
            }), status_code
        
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 503
        
    def _get_queue_stats(self):
        """Get queue statistics"""
        try:
            queue_lengths = self.queue_manager.get_all_queue_lengths()
            
            return jsonify({
                'queues': queue_lengths,
                'total': sum(queue_lengths.values())
            }), 200
        
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return jsonify({'error': str(e)}), 500
        
    def _clear_queues(self):
        """Clear all queues"""
        try:
            self.queue_manager.clear_all_queues()
            
            return jsonify({
                'message': 'All queues cleared',
                'queues_cleared': ['high', 'medium', 'low']
            }), 200
        
        except Exception as e:
            logger.error(f"Error clearing queues: {e}")
            return jsonify({'error': str(e)}), 500
        
    def _get_failed_articles(self):
        """Get all failed articles"""
        try:
            failed_articles = self.db.get_failed_articles()
            return jsonify({
                'total_failed': len(failed_articles),
                'articles': [article.to_dict() for article in failed_articles],
            }), 200
        
        except Exception as e:
            logger.error(f"Error fetching failed articles: {e}")
            return jsonify({'error': str(e)}), 500
        
    def _get_article(self, article_id: str):
        """Get single article by ID"""
        try:
            article = self.db.find_by_id(article_id)
            
            if not article:
                return jsonify({'error': 'Article not found'}), 404
            
            return jsonify(article.to_dict()), 200
        
        except Exception as e:
            logger.error(f"Error fetching article: {e}")
            return jsonify({'error': str(e)}), 500
        
    def run(self):
        """Run the Flask application"""
        self.app.run(
            host=self.settings.host,
            port=self.settings.port,
        )
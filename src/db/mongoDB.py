import logging
from typing import Optional, Any, Dict, List

from src.models.article import Article

from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import DuplicateKeyError, PyMongoError

logger = logging.getLogger(__name__)

class MongoDB:
    """
    Establish MongoDB connection
    """
    _instance = None

    def __new__(cls, settings):
        if not cls._instance:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance

    def __init__(self, settings):
        """
        Initialize MongoDB
        
        Args:
            settings: MongoDBConfig
        """
        if not hasattr(self, "_initialized"):
            self.settings = settings
            self.client = None
            self.db = None
            self.collection = None
            self._connect()
            self._initialized = True
    
    def _connect(self):
        """Establish MongoDB connection"""
        try: 
            
            self.client = MongoClient(self.settings.uri)
            
            self.client.server_info()
            
            self.db = self.client[self.settings.database]
            self.collection = self.db[self.settings.collection]
            
            # Create indexes
            self._create_indexes()
            
            logger.info(f"Connected to MongoDB: {self.settings.database}")
            
        except PyMongoError as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # Unique index on url_hash for deduplication
            self.collection.create_index(
                [('technical_metadata.url_hash', ASCENDING)],
                unique=True,
                name='url_hash_unique'
            )
            
            # Index on article id
            self.collection.create_index(
                [('id', ASCENDING)],
                name='article_id'
            )
            
            # Compound index for filtering and sorting
            self.collection.create_index([
                ('technical_metadata.status', ASCENDING),
                ('priority', ASCENDING),
                ('technical_metadata.scraped_date', DESCENDING)
            ], name='status_priority_date')
            
            # Indexes for filtering
            self.collection.create_index([('category', ASCENDING)], name='category')
            self.collection.create_index([('source', ASCENDING)], name='source')
            self.collection.create_index([('priority', ASCENDING)], name='priority')
            self.collection.create_index([('technical_metadata.scraped_date', DESCENDING)], name='scraped_date')
            
            logger.info("Database indexes created successfully")
            
        except PyMongoError as e:
            logger.warning(f"Error creating indexes (may already exist): {e}")

    def save(self, article: Article) -> bool:
        """
        Save or update article in database
        
        Args:
            article: Article object
            
        Returns:
            True if successful
        """
        try:
            article_dict = article.to_dict()
            
            # Try insert first
            self.collection.insert_one(article_dict)
            logger.info(f"Saved article {article.id} (status: {article.technical_metadata.status})")
            return True
            
        except DuplicateKeyError:
            # Article exists, update instead
            return self._update_duplicate(article)
            
        except PyMongoError as e:
            logger.error(f"Failed to save article {article.id}: {e}")
            return False
    
    def _update_duplicate(self, article: Article) -> bool:
        """Update existing article"""
        try:
            article_dict = article.to_dict()
            
            result = self.collection.replace_one(
                {'technical_metadata.url_hash': article.technical_metadata.url_hash},
                article_dict
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated existing article {article.id}")
                return True
            else:
                logger.warning(f"Article {article.id} exists but was not modified")
                return True
                
        except PyMongoError as e:
            logger.error(f"Failed to update duplicate article {article.id}: {e}")
            return False
    
    # TODO: Add this to API
    def find_by_id(self, article_id: str) -> Optional[Article]:
        """
        Find article by ID
        
        Args:
            article_id: Article ID
            
        Returns:
            Article object or None
        """
        try:
            doc = self.collection.find_one({'id': article_id}, {'_id': 0})
            if doc:
                return Article.from_dict(doc)
            return None
            
        except PyMongoError as e:
            logger.error(f"Error finding article {article_id}: {e}")
            return None
    
    def find_by_url_hash(self, url_hash: str) -> Optional[Article]:
        """Find article by URL hash"""
        try:
            doc = self.collection.find_one({'technical_metadata.url_hash': url_hash}, {'_id': 0})
            if doc:
                return Article.from_dict(doc)
            return None
            
        except PyMongoError as e:
            logger.error(f"Error finding article by URL hash: {e}")
            return None
    
    def find_by_status(self, status: str, limit: int = 100) -> List[Article]:
        """Find articles by status"""
        try:
            cursor = self.collection.find(
                {'technical_metadata.status': status},
                {'_id': 0}
            ).sort('scraped_at', DESCENDING).limit(limit)
            
            return [Article.from_dict(doc) for doc in cursor]
            
        except PyMongoError as e:
            logger.error(f"Error finding articles by status: {e}")
            return []
    
    def count_by_status(self, status: str) -> int:
        """Count articles by status"""
        try:
            return self.collection.count_documents({'technical_metadata.status': status})
        except PyMongoError as e:
            logger.error(f"Error counting articles: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {
                'total': self.collection.count_documents({}),
                'success': self.count_by_status('success'),
                'failed': self.count_by_status('failed'),
                'pending': self.count_by_status('pending')
            }
            
            stats['success_rate'] = (
                f"{(stats['success'] / stats['total'] * 100):.2f}%"
                if stats['total'] > 0 else "0%"
            )
            
            return stats
            
        except PyMongoError as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def get_failed_articles(self) -> List[Article]:
        """Get all failed articles"""
        return self.find_by_status('failed')
    
    def delete_by_id(self, article_id: str) -> bool:
        """Delete article by ID"""
        try:
            result = self.collection.delete_one({'id': article_id})
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Error deleting article: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all articles"""
        try:
            result = self.collection.delete_many({})
            logger.warning(f"Cleared {result.deleted_count} articles from database")
            return True
        except PyMongoError as e:
            logger.error(f"Error clearing database: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check MongoDB connection health"""
        try:
            self.client.server_info()
            return True
        except PyMongoError:
            return False
    
    def close(self):
        """Close MongoDB connection"""
        try:
            if self.client:
                self.client.close()
                logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
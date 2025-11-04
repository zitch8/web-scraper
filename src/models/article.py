import hashlib
from datetime import datetime

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

from src.models.scraped_metadata import ScrapedMetadata
from src.models.article_metadata import ArticleMetadata

@dataclass
class TechnicalMetadata:
    """Technical metadata for an article"""
    url_hash: str = ""
    scraped_date: str = None
    scraping_method: str = None
    status: str = "pending"
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class Article:
    """Compiled article metadata, scraped metadata, technical metadata"""
    
    # Original metadata
    id: str
    url: str
    source: str
    category: str
    priority: str

    scraped_metadata: Optional[ScrapedMetadata] = None
    technical_metadata: TechnicalMetadata = TechnicalMetadata()

    def __post_init__(self):
        """Generate url_hash if not provided"""
        if not self.technical_metadata.url_hash:
            self.url_hash = self._generate_url_hash()

    def _generate_url_hash(self) -> str:
        """Generate a SHA256 hash of the URL for deduplication"""
        return hashlib.sha256(self.url.encode()).hexdigest()

    def mark_success(self, scraped_metadata: ScrapedMetadata, method: str, processing_time: float):
        """Mark article as successfully processed"""
        self.scraped_metadata = scraped_metadata
        self.technical_metadata.status = "success"
        self.technical_metadata.scraped_date = datetime.now().isoformat()
        self.technical_metadata.scraping_method = method
        self.technical_metadata.processing_time = processing_time
        self.technical_metadata.error_message = None

    def mark_failed(self, error_message: str, method: str = "uknown"):
        """Mark article as failed"""
        self.technical_metadata.status = "failed"
        self.technical_metadata.scraping_method = method
        self.technical_metadata.scraped_date = datetime.now().isoformat()
        self.technical_metadata.error_message = error_message
        self.technical_metadata.retry_count += 1

    def should_use_selenium_fallback(self, technical_metadata: TechnicalMetadata) -> bool:
        """Determine if Selenium fallback should be used based"""
        if self.technical_metadata.status == "failed" and self.technical_metadata.scraping_method != "selenium":
            return True
        
        if self.scraped_metadata and not self.scraped_metadata.is_valid():
            return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            "id": self.id,
            "url": self.url,
            "source": self.source,
            "category": self.category,
            "priority": self.priority
        }
        if self.scraped_metadata:
            data["scraped_metadata"] = self.scraped_metadata.to_dict()

        if self.technical_metadata:
            data['technical_metadata'] = self.technical_metadata.to_dict()

        return data
    
    @classmethod
    def from_metadata(cls, metadata: ArticleMetadata) -> 'Article':
        """Create Article instance from ArticleMetadata"""
        return cls(
            id = metadata.id,
            url = metadata.url,
            source = metadata.source,
            category = metadata.category,
            priority = metadata.priority
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Article':
        """Create Article instance from data."""

        content_fields = {
            'title', 'description', 'keywords', 'author',
            'published_date', 'modified_date', 'images', 'canonical_url',
            'fb_app_id', 'fb_page_id', 'og_title', 'og_description', 'og_image',
            'og_site_name', 'article_publisher', 'og_type', 'twitter_card',
            'twitter_title', 'twitter_description', 'twitter_image', 'twitter_creator', 'twitter_site'
        }
        content_data = {}
        for key, value in data.items():
            if key in content_fields and value is not None:
                content_data[key] = value
        
        scraped_metadata = ScrapedMetadata(**content_data) if content_data else None


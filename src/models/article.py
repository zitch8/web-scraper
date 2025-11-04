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
        scraped_metadata = data.get("scraped_metadata")
        technical_metadata = data.get("technical_metadata")

        return cls(
            id=data["id"],
            url=data["url"],
            source=data["source"],
            category=data["category"],
            priority=data["priority"],
            scraped_metadata=scraped_metadata,
            technical_metadata=technical_metadata
        )
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class SocialMediaMetadata:
    facebook: Dict[str, Optional[str]] = None
    twitter: Dict[str, Optional[str]] = None

@dataclass
class ScrapedMetadata:
    """Scraped article data model"""

    # Scraped content
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    author: Optional[str] = None
    
    # Dates
    published_date: Optional[str] = None
    modified_date: Optional[str] = None

    # Media
    images: Optional[List[str]] = None
    canonical_url: Optional[str] = None

    # Social Media Metadata
    social_media: Optional[SocialMediaMetadata] = None

    # # Facebook Open Graph metadata
    # fb_app_id: Optional[str] = None
    # fb_page_id: Optional[str] = None
    # og_title: Optional[str] = None
    # og_description: Optional[str] = None
    # og_image: Optional[str] = None
    # og_site_name: Optional[str] = None
    # article_publisher: Optional[str] = None
    # og_type: Optional[str] = None

    # # Twitter Card metadata
    # twitter_card: Optional[str] = None
    # twitter_title: Optional[str] = None
    # twitter_description: Optional[str] = None
    # twitter_image: Optional[str] = None
    # twitter_creator: Optional[str] = None
    # twitter_site: Optional[str] = None

    def is_valid(self) -> bool:
        """Check if scraped content is valid (has at least a title)"""
        return bool(self.title)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
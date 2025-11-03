from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict

@dataclass
class SocialPlatformMetadata:
    publisher: Optional[str] = None
    properties: Dict[str, Optional[str]] = field(default_factory=dict)

@dataclass
class FacebookMetadata(SocialPlatformMetadata):
    page_id: Optional[str] = None
    app_id: Optional[str] = None

@dataclass
class TwitterMetadata(SocialPlatformMetadata):
    creator: Optional[str] = None
    card: Optional[str] = None

@dataclass
class SocialMediaMetadata:
    facebook: Optional[FacebookMetadata] = None
    twitter: Optional[TwitterMetadata] = None

@dataclass
class ScrapedMetadata:
    """Structured metadata extracted from an HTML document."""

    # Basic Metadata
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    author: Optional[str] = None
    site_name: Optional[str] = None

    # Dates
    published_date: Optional[str] = None
    modified_date: Optional[str] = None

    # Media
    image: Optional[str] = None
    canonical_url: Optional[str] = None

    # Social
    social_media: Optional[SocialMediaMetadata] = None

    def is_valid(self) -> bool:
        """Check if scraped content is valid (has at least a non-empty title)."""
        return bool(self.title and self.title.strip())

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary."""
        return asdict(self)

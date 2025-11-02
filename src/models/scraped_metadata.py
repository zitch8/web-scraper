from typing import Optional
from dataclasses import dataclass

@dataclass
class ScrapedArticle:
    """Scraped article data model"""
    id: str
    url: str
    title: str
    created_at: str  # ISO formatted datetime string
    updated_at: Optional[str]  # ISO formatted datetime string
    scraped_at: Optional[str] = None  # ISO formatted datetime string
    status: str = "pending"
    error_message: Optional[str] = None

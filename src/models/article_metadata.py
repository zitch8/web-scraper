import logging
from dataclasses import dataclass, asdict
from typing import Literal, Dict, Any

logger = logging.getLogger(__name__)

@dataclass
class ArticleMetadata:
    """Input article metadata from JSON"""
    id: str
    url: str
    source: str
    category: str
    priority: Literal["high", "medium", "low"]

    def validate(self) -> bool:
        """Validate article metadata fields."""
        try:
            if not isinstance(self.id, str):
                raise ValueError("Article id must be a string")

            if not isinstance(self.url, str) or not self.url.startswith(('http://', 'https://')):
                raise ValueError("Article url must be a valid URL string")

            if not isinstance(self.source, str):
                raise ValueError("Article source must be a string")

            if not isinstance(self.category, str):
                raise ValueError("Article category must be a string")

            if self.priority not in ("high", "medium", "low"):
                raise ValueError("Article priority must be 'high', 'medium', or 'low'")

            logger.debug(f"Validation successful for article: {self.id}")
            return True

        except ValueError as e:
            logger.error(f"Validation failed for article {getattr(self, 'id', None)}: {e}")
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary."""
        return asdict(self)

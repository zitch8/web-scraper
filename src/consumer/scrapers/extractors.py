import json
import logging
from bs4 import BeautifulSoup
from typing import Optional, List

from ...models.scraped_metadata import (
    ScrapedMetadata,
    SocialMediaMetadata,
    FacebookMetadata,
    TwitterMetadata,
)

logger = logging.getLogger(__name__)

class MetadataExtractor:
    """Extract structured metadata from HTML."""

    def extract(self, soup: BeautifulSoup) -> ScrapedMetadata:
        """Extract all required metadata from BeautifulSoup object."""

        content = ScrapedMetadata(
            social_media=SocialMediaMetadata(
                facebook=FacebookMetadata(),
                twitter=TwitterMetadata(),
            )
        )

        # Basic Metadata
        content.title = self._extract_title(soup)
        content.description = self._extract_description(soup)
        content.keywords = self._extract_keywords(soup)
        content.author = self._extract_author(soup)
        content.site_name = self._get_first_meta_content(soup, "og:site_name")

        # Dates
        content.published_date = self._extract_publish_date(soup)
        content.modified_date = self._extract_modified_date(soup)

        # Media
        content.image = self._extract_image(soup)
        content.canonical_url = self._extract_canonical_url(soup)

        # Social Media
        fb = content.social_media.facebook
        fb.publisher = self._extract_publisher(soup)
        fb.page_id = self._get_meta_content(soup, "fb:pages")
        fb.app_id = self._get_meta_content(soup, "fb:app_id")

        tw = content.social_media.twitter
        tw.publisher = self._get_meta_content(soup, "twitter:site")
        tw.creator = self._get_meta_content(soup, "twitter:creator")
        tw.card = self._get_meta_content(soup, "twitter:card")

        logger.debug("Extracted metadata: %s", json.dumps(content.to_dict(), indent=2))
        return content


    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title."""
        return (
            self._get_tag_text(soup, "title")
            or self._get_first_meta_content(soup, "og:title", "twitter:title")
        )

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description."""
        return self._get_first_meta_content(
            soup, "description", "og:description", "twitter:description"
        )

    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract keywords as list."""
        keywords_str = self._get_meta_content(soup, "keywords")
        return [k.strip() for k in keywords_str.split(",")] if keywords_str else []

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author from meta or link."""
        return (
            self._get_meta_content(soup, "author")
            or self._get_meta_content(soup, "article:author")
            or self._get_tag_text(soup, "a", {"rel": "author"})
        )

    def _extract_publisher(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publisher from Open Graph."""
        return self._get_first_meta_content(
            soup, "article:publisher", "og:site_name", "twitter:site"
        )

    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article publish date."""
        return self._get_first_meta_content(
            soup, "article:published_time", "publish_date", "pubdate"
        ) or self._get_tag_attr(soup, "time", "datetime")

    def _extract_modified_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article modification date."""
        return self._get_first_meta_content(
            soup, "article:modified_time", "last-modified", "updated_time"
        )

    def _extract_image(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main image."""
        return self._get_first_meta_content(
            soup, "og:image", "twitter:image", "image"
        ) or self._get_link_href(soup, "image_src")

    def _extract_canonical_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract canonical URL."""
        return (
            self._get_link_href(soup, "canonical")
            or self._get_meta_content(soup, "og:url")
        )

    def _get_meta_content(self, soup: BeautifulSoup, property_name: str) -> Optional[str]:
        """Get meta tag content by property or name."""
        tag = soup.find("meta", property=property_name) or soup.find(
            "meta", attrs={"name": property_name}
        )
        return tag["content"].strip() if tag and tag.get("content") else None

    def _get_first_meta_content(self, soup: BeautifulSoup, *names: str) -> Optional[str]:
        """Return the first available meta content from given names."""
        for name in names:
            content = self._get_meta_content(soup, name)
            if content:
                return content
        return None

    def _get_tag_text(self, soup: BeautifulSoup, tag: str, attrs: dict = None) -> Optional[str]:
        """Return tag text if present."""
        t = soup.find(tag, attrs=attrs)
        return t.get_text(strip=True) if t else None

    def _get_tag_attr(self, soup: BeautifulSoup, tag: str, attr: str) -> Optional[str]:
        """Return attribute value from tag."""
        t = soup.find(tag, attrs={attr: True})
        return t[attr].strip() if t and t.get(attr) else None

    def _get_link_href(self, soup: BeautifulSoup, rel: str) -> Optional[str]:
        """Return href from link[rel]."""
        tag = soup.find("link", attrs={"rel": rel})
        return tag["href"].strip() if tag and tag.get("href") else None

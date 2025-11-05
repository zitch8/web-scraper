
# Web Scraper

## 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd web-scraper

# Create virtual environment
python -m venv .venv
.venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# (Or manually create .env and copy structure from .env.example)
```

## 2. Configuration

### Environment Variables (.env)
```
# Example values
REDIS_HOST=localhost
REDIS_PORT=6379

MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=scraper
MONGODB_COLLECTION=scraped_articles

DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = 5000
```

### YAML Config (src/config/config.yaml)
All runtime parameters (Redis queues, scraper options, consumer/publisher behavior, etc.) can be modified from `config.yaml` for centralized control.

## 3. Infrastructure Setup

### Redis Setup
```
# For Windows users:
# Install WSL (Windows Subsystem for Linux)

# Then open your Linux terminal
sudo apt install redis-server

# Start Redis
sudo service redis-server start

# Verify the connection
redis-cli
> ping
PONG
```

### MongoDB Setup
```
# Create database
use scraper

# Create collection
db.createCollection("scraped_articles")
```

## 4. Running the Services

### Terminal 1 — Start Publisher
```bash
python src/scripts/run_publisher.py
```

### Terminal 2 — Start Consumer
```bash
python src/scripts/run_consumer.py
```

### Terminal 3 — Start Dashboard
```bash
python src/scripts/run_dashboard.py
```

## 5. Features

- **Priority-Based Queues**
  Consumes messages in order of priority (high > medium > low) using Redis.

- **Selenium Fallback Strategy**
  Automatically switches to Selenium for JavaScript-rendered pages.

- **Deduplication**
  Uses SHA256 hashing + MongoDB unique index on `url_hash` to prevent duplicates.

- **Centralized Configuration**
  All components are configurable from a single YAML and `.env` file.

- **Retry Logic**
  Automatically retries failed scrapes with backoff and configurable limits.

- **Metrics & Analytics**
  Tracks total processed articles, success/failure rates, and per-method stats.

- **Comprehensive Logging**
  Logs all operations, including queue interactions, scraping, and database results.

- **Comprehensive Article Metadata Extraction**
  Extracts:
  - Content Metadata: title, description, author, publish_date, modified_date, image_url, canonical_url, keywords
  - Social Media Metadata: facebook, twitter
  - Technical Metadata: url_hash, scraped_date, scraping_method, status, error_message, processing_time, retry_count

- **Dashboard Flask API**
  Dashboard API runs on http://127.0.0.1:5000
  then add this endpoints to view content. (Ex: http://127.0.0.1:5000/health )
  Available endpoints:
  - GET  /health          - Health check
  - GET  /articles/<id>   - Get single article
  - GET  /articles/failed - Get failed articles
  - GET  /queue/stats     - Queue statistics
  - POST /queue/clear     - Clear all queues

## 6. File Structure

```
web-scraper
├── data/
├── logs/
├── src/
│   ├── config/
│   │   ├── config.yaml
│   │   ├── logging.ini
│   │   ├── logging_config.py
│   │   ├── settings.py
│   ├── publisher/
│   │   └── redis_queue.py
│   ├── db/
│   │   └── mongoDB.py
│   ├── models/
│   │   ├── article_metadata.py
│   │   ├── article.py
│   │   └── scraped_metadata.py
│   ├── consumer/
│   │   ├── base_scraper.py
│   │   ├── bs_scraper.py
│   │   ├── selenium_scraper.py
│   │   └── extractors.py
│   ├── api/
│   │   └── dashboard.py
│   ├── scripts/
│   │   ├── run_publisher.py
│   │   └── run_consumer.py
│   │   └── run_dashboard.py
│   ├── services/
│   │   ├── consumer.py
│   │   └── publisher.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 7. Database Schema / Model

### Article Model

| Field | Type | Description |
|-------|------|-------------|
| `title` | `str` | Article title |
| `description` | `str` | Article summary or description |
| `keywords` | `list[str]` | List of keywords extracted from metadata |
| `author` | `str` | Author of the article |
| `site_name` | `str` | Source or site name |
| `published_date` | `datetime` | Article publish date |
| `modified_date` | `datetime` | Last modification date |
| `image` | `str` | Main image URL |
| `canonical_url` | `str` | Canonical link for the article |
| `social_media.facebook.publisher` | `str` | Facebook page URL |
| `social_media.facebook.page_id` | `str` | Facebook Page ID |
| `social_media.facebook.app_id` | `str` | Facebook App ID |
| `social_media.twitter.publisher` | `str` | Twitter publisher |
| `social_media.twitter.creator` | `str` | Twitter creator |
| `social_media.twitter.card` | `str` | Twitter card type |
| `technical_metadata.url_hash` | `str` | SHA256 hash for deduplication |
| `technical_metadata.scraped_date` | `datetime` | Date when scraped |
| `technical_metadata.scraping_method` | `str` | Scraping method used |
| `technical_metadata.status` | `str` | Scrape result status |
| `technical_metadata.error_message` | `str` | Error message if failed |
| `technical_metadata.processing_time` | `float` | Time taken to scrape |
| `technical_metadata.retry_count` | `int` | Number of retries |

**MongoDB Indexes**
- `url_hash` > unique index for deduplication
- `id`, `priority`, `scraped_at` > compound index for performance
- Additional indexes for `source`, `category`, and `priority`

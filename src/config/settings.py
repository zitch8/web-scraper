from dataclasses import dataclass
from typing import Any, Dict, List
from pathlib import Path

import os
import yaml
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

@dataclass
class RedisConfig:
    """Redis client configuration."""
    host: str = os.getenv('REDIS_HOST')
    port: int = int(os.getenv('REDIS_PORT'))
    db: int
    socket_timeout: int
    decode_responses: bool
    max_connections: int

    # Queue names
    queue_high: str
    queue_medium: str
    queue_low: str

    def get_queue_names(self, priority: str) -> str:
        """Return a list of all queue names."""
        priority_map = {
            'high': self.queue_high,
            'medium': self.queue_medium,
            'low': self.queue_low
        }
        return priority_map.get(priority.lower(), self.queue_low)

    def to_client_kwargs(self) -> Dict[str, Any]:
        """Return a dictionary of Redis client keyword arguments."""
        return {
            'host': self.host,
            'port': self.port,
            'db': self.db,
            'socket_timeout': self.socket_timeout,
            'decode_responses': self.decode_responses,
            'max_connections': self.max_connections
        }
    
@dataclass
class MongoDBConfig:
    """MongoDB client configuration."""
    uri: str = os.getenv('MONGODB_URI')
    database_name: str = os.getenv('MONGODB_DATABASE')
    collection_name: str = os.getenv('MONGODB_COLLECTION')
    
    def to_client_kwargs(self) -> Dict[str, Any]:
        """Return a dictionary of MongoDB client keyword arguments."""
        return {
            'uri': self.uri,
            'database_name': self.database_name,
            'collection_name': self.collection_name
        }
    
@dataclass
class RequestsConfig:
    """Requests library client configuration."""
    timeout: int
    max_retries: int
    retry_delay: int

    # TODO: Add proxy settings

    # TODO: Add user-agent settings

    def to_client_kwargs(self) -> Dict[str, Any]:
        """Return a dictionary of Requests client keyword arguments."""
        return {
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay
        }

@dataclass
class SeleniumConfig:
    """Selenium WebDriver client configuration."""
    headless: bool
    implicit_wait: int
    timeout: int
    no_sandbox: bool

    enabled_fallback: bool
    required_elements: List[str]

    # Return Chrome options if needed
    def get_chrome_options(self):
        """Return Chrome options based on the configuration."""
        from selenium.webdriver.chrome.options import Options
        
        options = Options()

        if self.headless:
            options.add_argument('--headless')
        
        if self.no_sandbox:
            options.add_argument('--no-sandbox')
        
        return options
    
    def should_use_fallback(self, has_title: bool) -> bool:
        """Determine if Selenium fallback should be used based on parsed HTML."""
        if not self.enabled_fallback:
            return False
        
        if "title" in self.required_elements and not has_title:
            return True
        
        return False

@dataclass
class ScraperConfig:
    request: RequestsConfig
    selenium: SeleniumConfig

@dataclass
class ConsumerConfig:
    # TODO: Add consumer-specific configurations
    pass

@dataclass
class PublisherConfig:
    # TODO: Add publisher-specific configurations
    pass

@dataclass
class DashboardConfig:
    host: str
    port: int

    enable_cors: bool
    cors_origins: str

    def __post_init__(self):
        self.host = os.getenv('DASHBOARD_HOST')
        self.port = int(os.getenv('DASHBOARD_PORT'))


class Settings:
    """
    Centralized settings class for all clients and services
    """
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Load YAML configuration file
        yaml_config = self._load_yaml_config()
        self._init_configs(yaml_config)
        self._initialized = True
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from a YAML file."""
        yaml_file_path = Path(__file__).resolve().parent.parent / 'config.yaml'
        if yaml_file_path.exists():
            with open(yaml_file_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def _init_configs(self, yaml_config: Dict[str, Any]):
        """Initialize all configuration dataclasses."""
        
        # Redis
        redis_yaml = yaml_config.get('redis', {})
        self.redis = RedisConfig()
        self._updated_from_yaml(self.redis, redis_yaml)

        # MongoDB
        mongodb_yaml = yaml_config.get('mongodb', {})
        self.mongodb = MongoDBConfig()
        self._updated_from_yaml(self.mongodb, mongodb_yaml)

        # Scraper
        scraper_yaml = yaml_config.get('scraper', {})

        # Requests
        requests_yaml = scraper_yaml.get('request', {})
        self.scraper = ScraperConfig()
        self._updated_from_yaml(self.scraper.request, requests_yaml)

        # Selenium
        selenium_yaml = scraper_yaml.get('selenium', {})
        self._updated_from_yaml(self.scraper.selenium, selenium_yaml)

        # Dashboard
        dashboard_yaml = yaml_config.get('dashboard', {})
        self.dashboard = DashboardConfig()
        self._updated_from_yaml(self.dashboard, dashboard_yaml)

    def _updated_from_yaml(self, config_instance, yaml_section: Dict[str, Any]):
        """Update a dataclass instance with values from a YAML section."""
        for key, value in yaml_section.items():
            if hasattr(config_instance, key):
                setattr(config_instance, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert all configurations to a dictionary."""
        return {
            'redis': self.redis,
            'mongodb': self.mongodb,
            'scraper': {
                'request': self.scraper.request,
                'selenium': self.scraper.selenium
            },
            'dashboard': self.dashboard
        }

    def reload(self):
        """Reload configuration from environment variables and YAML file."""
        load_dotenv(override=True)
        yaml_config = self._load_yaml_config()
        self._init_configs(yaml_config)

    def validate(self) -> bool:
        """Validate the current configuration settings."""
        errors = []

        if not self.redis.host:
            errors.append("Redis host is not set.")

        if not self.mongodb.uri:
            errors.append("MongoDB URI is not set.")
        
        return (len(errors) == 0, errors)
    

settings = Settings()
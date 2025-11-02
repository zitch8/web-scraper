from dataclasses import dataclass
from typing import Any, Dict
from pathlib import Path

import os
import yaml
from dotenv import load_dotenv

@dataclass
class RedisConfig:
    """Redis client configuration."""
    host: str
    port: int
    db: int
    socket_timeout: int
    decode_responses: bool
    max_connections: int

    # Queue names
    queue_high: str
    queue_medium: str
    queue_low: str

    def __post_init__(self):
        self.host = os.getenv('REDIS_HOST')
        self.port = int(os.getenv('REDIS_PORT'))

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
    uri: str
    database_name: str
    collection_name: str

    def __post_init__(self):
        self.uri = os.getenv('MONGODB_URI')
        self.database_name = os.getenv('MONGODB_DATABASE')
        self.collection_name = os.getenv('MONGODB_COLLECTION')
    
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
    no_sandbox: bool

    def to_client_kwargs(self) -> Dict[str, Any]:
        """Return a dictionary of Selenium WebDriver client keyword arguments."""
        return {
            'headless': self.headless,
            'implicit_wait': self.implicit_wait,
            'no_sandbox': self.no_sandbox
        }

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

@dataclass
class ScraperConfig:
    requests: RequestsConfig
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
        
        # Load environment variables from .env file
        env_path = Path(__file__).resolve().parent.parent.parent / '.env'
        load_dotenv(dotenv_path=env_path)

        # Load YAML configuration file
        yaml_config = self._load_yaml_config()
        self._init_configs(yaml_config)
        self._initialized = True
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from a YAML file."""
        yaml_file_path = Path(__file__).resolve().parent / 'config.yaml'
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
        self.scraper = ScraperConfig()

        # Requests
        requests_yaml = scraper_yaml.get('requests', {})
        self._updated_from_yaml(self.scraper.requests, requests_yaml)

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
    
    def __repr__(self):
        return (f"Settings(redis={self.redis.host}:{self.redis.port}, mongodb={self.mongodb.database_name}")

settings = Settings()



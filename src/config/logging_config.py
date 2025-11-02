import logging
import logging.config
from pathlib import Path

def logging_config(service_name: str = 'app'):
    """Set up centralized logging configuration."""
    CONFIG_PATH = Path(__file__).resolve().parent / "logging.ini"
    LOG_DIR = Path(__file__).parent.parent / 'logs'
    LOG_DIR.mkdir(exist_ok=True)

    # Modify logging.ini to set dynamic log file path
    log_ini = CONFIG_PATH.read_text()
    updated_log_ini = log_ini.replace('{log_path}', str(LOG_DIR / f"{service_name}.log"))

    temp_config = LOG_DIR / f"temp_{service_name}_logging.ini"
    temp_config.write_text(updated_log_ini)

    logging.config.fileConfig(temp_config, disable_existing_loggers=False)
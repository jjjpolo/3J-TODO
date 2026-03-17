import logging
from logging.handlers import RotatingFileHandler
import json
import os
from services.app_paths import get_runtime_file, get_bundled_file

CONFIG_FILE = get_runtime_file('config.json')
LOG_FILE = get_runtime_file('app.log')

DEFAULT_CONFIG = {
    'default_tab': 'Personal',
    'show_completed': False,
    'log_level': 'INFO',
}


def _load_or_create_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    merged = dict(DEFAULT_CONFIG)
                    merged.update(data)
                    return merged
        except (OSError, json.JSONDecodeError):
            pass

    bundled_config = get_bundled_file('config.json')
    if os.path.exists(bundled_config):
        try:
            with open(bundled_config, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    merged = dict(DEFAULT_CONFIG)
                    merged.update(data)
                    with open(CONFIG_FILE, 'w', encoding='utf-8') as out:
                        json.dump(merged, out, indent=2)
                    return merged
        except (OSError, json.JSONDecodeError):
            pass

    with open(CONFIG_FILE, 'w', encoding='utf-8') as out:
        json.dump(DEFAULT_CONFIG, out, indent=2)
    return dict(DEFAULT_CONFIG)

# Load config
config = _load_or_create_config()

LOG_LEVEL = getattr(logging, config.get('log_level', 'INFO').upper(), logging.INFO)

logger = logging.getLogger('todo_app')
logger.setLevel(LOG_LEVEL)
if not logger.handlers:
    handler = RotatingFileHandler(LOG_FILE, maxBytes=1024*1024, backupCount=3)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Example usage:
# logger.info('App started')
# logger.debug('Debug message')
# logger.warning('Warning message')
# logger.error('Error message')
# logger.critical('Critical error')

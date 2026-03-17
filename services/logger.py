import logging
from logging.handlers import RotatingFileHandler
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), '../config.json')
LOG_FILE = os.path.join(os.path.dirname(__file__), '../app.log')

# Load config
with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

LOG_LEVEL = getattr(logging, config.get('log_level', 'INFO').upper(), logging.INFO)

logger = logging.getLogger('todo_app')
logger.setLevel(LOG_LEVEL)
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

from utils.logger import logger
import os
import json

def local_config(config_path=None):
    CONFIG_PATH = config_path or os.getenv("CONFIG_PATH")
    logger.info(f"Using config path: {CONFIG_PATH}")

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"An error occurred while reading config: {e}")
        return None 


def config_source(key, default=None, config_path=None):
    config = local_config(config_path)
    if key in os.environ:
        return os.getenv(key)
    return config.get(key, default)
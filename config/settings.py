# (INPROGRESS) Testing after cleaning

import configparser
from pathlib import Path
from utils.helpers import get_project_root
#from dotenv import load_dotenv  # to support .env

# Load .env if present
#load_dotenv()

PROJECT_ROOT = get_project_root(levels_up=1)

def load_config(filename="config.ini", folder="config"):
    """Loads configuration from config file."""
    project_root = get_project_root(levels_up=1)
    config_path = project_root / folder / filename
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at: {config_path}")
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

config = load_config()


# / after Path object, returns Path. resolve() for absolute path
# access with PARENT_FOLDERS[], instead of .get(), for quicker fails

ALPHA_VANTAGE_CONFIG = {
    "api_key": config.get("alpha_vantage", "api_key"), # , fallback=os.environ.get("ALPHA_VANTAGE_API_KEY")
    "api_url": config.get("alpha_vantage", "api_url"),  # , fallback=os.environ.get("ALPHA_VANTAGE_API_URL")
    "base_filename": config.get("alpha_vantage", "base_filename"),
    }

ALPHA_VANTAGE_PATHS = {
    key: (PROJECT_ROOT / config.get("alpha_vantage", key)).resolve()  
    for key in [
        "folder_raw",
        "folder_clean",
        "folder_processed",
        "folder_resampled"
        ]
    }

NEWSDATA_CONFIG = {
    "api_key": config.get("newsdata", "api_key"), # , fallback=os.environ.get("NEWSDATA_API_KEY")
    "api_url": config.get("newsdata", "api_url"),  # , fallback=os.environ.get("NEWSDATA_API_URL")
    "news_per_request": config.get("newsdata", "news_per_request"),
    "max_requests": config.get("newsdata", "max_requests"),
    "max_search_terms": config.get("newsdata", "max_search_terms"),
    "base_filename": config.get("newsdata", "base_filename")
    }


NEWSDATA_PATHS = {
    key: (PROJECT_ROOT / config.get("newsdata", key)).resolve()  # absolute paths
    for key in [
        "folder_raw",
        "folder_clean",
        "folder_processed",
        "folder_resampled"
        ]
    }

PARENT_FOLDERS = {
    key: (PROJECT_ROOT / config.get("parent_folders", key)).resolve()
    for key in [
        "parent_data",
        "parent_raw",
        "parent_clean",
        "parent_processed",
        "parent_resampled",
        "parent_merged",
        "parent_backup",
        "parent_log",
        ]
    }

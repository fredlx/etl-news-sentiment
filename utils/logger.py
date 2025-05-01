# (DONE) utils.logger.py
"""
Stick to:
ETL Step	Log Example

Extract:	"Extracting data" + search terms
Transform:	"Applying transformation"
Validate:	"Checking schema" + list of columns
Load:	"Saving file" + filename, rows saved
Error:	"Extraction failed" + reason/context

"""

import logging
import os
from pathlib import Path

# Base directory (folder where this script lives)
BASE_DIR = Path(__file__).resolve().parent.parent  # (REFACTOR)
LOG_DIR = BASE_DIR / "logs"

# Create logs/ folder if it doesn't exist
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE_PATH = LOG_DIR / "etl.log"

def setup_logger(name="etl", log_file=LOG_FILE_PATH, level=logging.INFO):
    logger = logging.getLogger(name)

    if not logger.handlers:  # prevent duplicate handlers
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.setLevel(level)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


def clear_log_file():
    if not os.path.isfile(LOG_FILE_PATH):
        print(f"Error: '{LOG_FILE_PATH}' does not exist or is not a file.")
        return

    def get_file_size_mb(filepath):
        """Returns the file size in megabytes."""
        size_bytes = os.path.getsize(filepath)
        size_mb = size_bytes / (1024 * 1024)
        return size_mb

    size_before = get_file_size_mb(LOG_FILE_PATH)
    print(f"File size before clearing: {size_before:.4f} MB")

    # Ask for confirmation
    confirm = input(f"Are you sure you want to clear '{LOG_FILE_PATH}'? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Aborted. Log file was not cleared.")
        return

    with open(LOG_FILE_PATH, 'w') as file:
        file.truncate(0)

    size_after = get_file_size_mb(LOG_FILE_PATH)
    print(f"File size after clearing: {size_after:.4f} MB")
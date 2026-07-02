import logging
from pathlib import Path

#
# Configure the minimum level to log (Default is WARNING)
logging.basicConfig(level=logging.DEBUG)

SQLITE_DATABASE_NAME = "mcp_hunter.db"


# Anchor to project root (one level up from this file)
ROOT_DIR = Path(__file__).parent
FETCHED_REPOSITORY_DATA_DIR = f"{ROOT_DIR}/repos/"
SEMGREP_RULES_DIR = f"{ROOT_DIR}/rules/"

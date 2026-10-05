import os

DB_CONFIG = {
    "host": os.environ.get("WAREHOUSE_DB_HOST", "localhost"),
    "port": os.environ.get("WAREHOUSE_DB_PORT", "5432"),
    "user": os.environ.get("WAREHOUSE_DB_USER", "warehouse"),
    "password": os.environ.get("WAREHOUSE_DB_PASSWORD", "warehouse"),
    "dbname": os.environ.get("WAREHOUSE_DB_NAME", "warehouse_db"),
}

TRACKED_UNIVERSE_SIZE = int(os.environ.get("TRACKED_UNIVERSE_SIZE", "25"))
HISTORICAL_DAYS = int(os.environ.get("HISTORICAL_DAYS", "180"))
API_BASE = os.environ.get("COINGECKO_API_BASE", "https://api.coingecko.com/api/v3")
REQUEST_DELAY_SECONDS = float(os.environ.get("REQUEST_DELAY_SECONDS", "10"))
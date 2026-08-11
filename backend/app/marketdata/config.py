import os
from pathlib import Path

from dotenv import load_dotenv


# Local development uses the repository-level .env. `override=False` keeps
# explicitly supplied process environment variables authoritative.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env", override=False)


ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
ALPHAVANTAGE_BASE = os.getenv("ALPHAVANTAGE_BASE", "https://www.alphavantage.co")

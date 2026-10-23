"""Load environment and configuration for PersonaInvest."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (Investanalyser/)
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_env_path)


def get_env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


# API keys
UPSTOX_ACCESS_TOKEN = get_env("UPSTOX_ACCESS_TOKEN")
HDFC_API_KEY = get_env("HDFC_API_KEY")
HDFC_API_SECRET = get_env("HDFC_API_SECRET")
GEMINI_API_KEY = get_env("GEMINI_API_KEY") or get_env("GOOGLE_API_KEY")
TAVILY_API_KEY = get_env("TAVILY_API_KEY")

# Toggle: use mock portfolio when True (no broker APIs required)
USE_MOCK_DATA = get_env("USE_MOCK_DATA", "false").lower() in ("true", "1", "yes")

# Upstox API base
UPSTOX_BASE_URL = "https://api.upstox.com/v2"

# HDFC InvestRight base (typical pattern; adjust per official docs)
HDFC_BASE_URL = get_env("HDFC_BASE_URL", "https://api.hdfcsec.com")

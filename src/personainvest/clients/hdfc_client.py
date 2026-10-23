"""HDFC Securities InvestRight Individual API client for positions."""

import logging
from typing import Any

import requests

from personainvest.config import HDFC_API_KEY, HDFC_API_SECRET, HDFC_BASE_URL
from personainvest.models import HoldingItem, PortfolioState

logger = logging.getLogger(__name__)

# Typical InvestRight positions endpoint (adjust per official HDFC API docs)
POSITIONS_PATH = "/api/v1/positions"
POSITIONS_URL = f"{HDFC_BASE_URL.rstrip('/')}{POSITIONS_PATH}"


def fetch_hdfc_positions() -> PortfolioState:
    """
    Fetch positions from HDFC InvestRight and return standardized PortfolioState.
    If credentials are missing or API fails, returns empty state (no exception).
    """
    if not HDFC_API_KEY or not HDFC_API_SECRET:
        logger.warning("HDFC API keys not set; returning empty HDFC portfolio.")
        return PortfolioState(holdings=[], as_of_text="HDFC: no credentials")

    # HDFC often uses API key in header and signature/secret for auth; adjust per docs
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-API-Key": HDFC_API_KEY,
    }
    # If HDFC uses Bearer after OAuth, set Authorization instead; adapt as per docs
    try:
        resp = requests.get(POSITIONS_URL, headers=headers, timeout=15)
        if resp.status_code == 429:
            logger.warning("HDFC rate limit (429); returning empty state.")
            return PortfolioState(holdings=[], as_of_text="HDFC: rate limited")
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.warning("HDFC positions request failed (use mock or check docs): %s", e)
        return PortfolioState(holdings=[], as_of_text="HDFC: request failed")

    data = resp.json()
    raw_list = data.get("data") or data.get("positions") or []
    if isinstance(data, list):
        raw_list = data
    if not raw_list:
        return PortfolioState(holdings=[], as_of_text="HDFC: no positions")

    holdings: list[HoldingItem] = []
    total_value = 0.0
    for row in raw_list:
        if not isinstance(row, dict):
            continue
        item = _row_to_holding(row)
        if item:
            holdings.append(item)
            total_value += item.last_price * item.quantity

    return PortfolioState(
        holdings=holdings,
        total_value=round(total_value, 2),
        as_of_text="HDFC InvestRight",
    )


def _row_to_holding(row: dict[str, Any]) -> HoldingItem | None:
    """Map HDFC position row to HoldingItem (field names may vary per API version)."""
    try:
        ticker = (
            (row.get("trading_symbol") or row.get("symbol") or row.get("tradingsymbol") or "")
        ).strip()
        if not ticker:
            return None
        qty = int(row.get("quantity", 0) or row.get("qty", 0) or 0)
        if qty <= 0:
            return None
        avg = float(row.get("average_price", 0) or row.get("avg_price", 0) or 0)
        last = float(row.get("last_price", 0) or row.get("ltp", 0) or row.get("close", 0) or 0)
        if last <= 0:
            last = avg
        pnl = float(row.get("pnl", 0) or row.get("profit_loss", 0) or 0)
        cost = avg * qty
        pnl_pct = (pnl / cost * 100) if cost else 0
        return HoldingItem(
            ticker=ticker,
            isin=str(row.get("isin", "") or ""),
            company_name=str(row.get("company_name", "") or row.get("name", "") or "").strip(),
            quantity=qty,
            average_price=avg,
            last_price=last,
            pnl=pnl,
            pnl_percent=round(pnl_pct, 2),
            exchange=str(row.get("exchange", "NSE") or "NSE"),
            source="HDFC",
        )
    except (TypeError, ValueError):
        return None

"""Upstox API v2 client for long-term holdings."""

import logging
from typing import Any

import requests

from personainvest.config import UPSTOX_ACCESS_TOKEN, UPSTOX_BASE_URL
from personainvest.models import HoldingItem, PortfolioState

logger = logging.getLogger(__name__)

HOLDINGS_URL = f"{UPSTOX_BASE_URL}/portfolio/long-term-holdings"


def fetch_upstox_holdings() -> PortfolioState:
    """
    Fetch long-term holdings from Upstox and return a standardized PortfolioState.
    Raises on auth/network errors; returns empty state on empty response.
    """
    if not UPSTOX_ACCESS_TOKEN:
        logger.warning("UPSTOX_ACCESS_TOKEN not set; returning empty Upstox portfolio.")
        return PortfolioState(holdings=[], as_of_text="Upstox: no token")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}",
    }
    try:
        resp = requests.get(HOLDINGS_URL, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            logger.warning("Upstox rate limit (429); returning empty state.")
            return PortfolioState(holdings=[], as_of_text="Upstox: rate limited")
        raise
    except requests.exceptions.RequestException as e:
        logger.exception("Upstox request failed: %s", e)
        raise

    data = resp.json()
    raw_list = data.get("data") if isinstance(data, dict) else []
    if not raw_list:
        return PortfolioState(holdings=[], as_of_text="Upstox: no holdings")

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
        as_of_text="Upstox (long-term holdings)",
    )


def _row_to_holding(row: dict[str, Any]) -> HoldingItem | None:
    """Map Upstox holding row to HoldingItem."""
    try:
        qty = int(row.get("quantity", 0) or 0)
        if qty <= 0:
            return None
        avg = float(row.get("average_price", 0) or 0)
        last = float(row.get("last_price", 0) or row.get("close_price", 0) or 0)
        pnl = float(row.get("pnl", 0) or 0)
        cost = avg * qty
        pnl_pct = (pnl / cost * 100) if cost else 0
        ticker = (row.get("trading_symbol") or row.get("tradingsymbol") or "").strip()
        if not ticker:
            return None
        return HoldingItem(
            ticker=ticker,
            isin=str(row.get("isin", "") or ""),
            company_name=str(row.get("company_name", "") or "").strip(),
            quantity=qty,
            average_price=avg,
            last_price=last,
            pnl=pnl,
            pnl_percent=round(pnl_pct, 2),
            exchange=str(row.get("exchange", "NSE") or "NSE"),
            source="Upstox",
        )
    except (TypeError, ValueError):
        return None

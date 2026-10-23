"""Aggregate portfolio from Upstox, HDFC, or mock."""

from personainvest.config import USE_MOCK_DATA
from personainvest.models import HoldingItem, PortfolioState
from personainvest.clients import (
    fetch_upstox_holdings,
    fetch_hdfc_positions,
    get_mock_portfolio_state,
)


def get_portfolio_state(use_mock: bool | None = None) -> PortfolioState:
    """
    Return a single PortfolioState. If use_mock is True or USE_MOCK_DATA is True,
    return mock data. Otherwise merge Upstox + HDFC (dedupe by ticker, prefer first).
    """
    if use_mock is None:
        use_mock = USE_MOCK_DATA
    if use_mock:
        return get_mock_portfolio_state()

    upstox = fetch_upstox_holdings()
    hdfc = fetch_hdfc_positions()
    return merge_portfolio_states(upstox, hdfc)


def merge_portfolio_states(
    a: PortfolioState, b: PortfolioState
) -> PortfolioState:
    """Merge two portfolio states; same ticker from same exchange is summed (qty, value)."""
    by_key: dict[tuple[str, str], HoldingItem] = {}
    for h in a.holdings + b.holdings:
        key = (h.ticker, h.exchange)
        if key in by_key:
            existing = by_key[key]
            total_qty = existing.quantity + h.quantity
            if total_qty <= 0:
                continue
            total_cost = existing.average_price * existing.quantity + h.average_price * h.quantity
            avg_price = total_cost / total_qty
            last = h.last_price or existing.last_price
            pnl = (last - avg_price) * total_qty
            pnl_pct = (pnl / (avg_price * total_qty) * 100) if avg_price else 0
            by_key[key] = HoldingItem(
                ticker=existing.ticker,
                isin=existing.isin or h.isin,
                company_name=existing.company_name or h.company_name,
                quantity=total_qty,
                average_price=round(avg_price, 2),
                last_price=last,
                pnl=round(pnl, 2),
                pnl_percent=round(pnl_pct, 2),
                exchange=existing.exchange,
                source=f"{existing.source}+{h.source}",
            )
        else:
            by_key[key] = h

    holdings = list(by_key.values())
    total_value = sum(h.last_price * h.quantity for h in holdings)
    as_of = " | ".join(filter(None, [a.as_of_text, b.as_of_text]))
    return PortfolioState(
        holdings=holdings,
        total_value=round(total_value, 2),
        as_of_text=as_of or "Merged",
    )

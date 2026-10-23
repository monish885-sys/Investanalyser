"""Mock portfolio data for testing without broker API credentials."""

from personainvest.models import HoldingItem, PortfolioState


def get_mock_portfolio_state() -> PortfolioState:
    """Return a realistic mock PortfolioState for Indian equities."""
    holdings = [
        HoldingItem(
            ticker="RELIANCE",
            isin="INE002A01018",
            company_name="Reliance Industries Ltd",
            quantity=10,
            average_price=2450.0,
            last_price=2520.0,
            pnl=700.0,
            pnl_percent=2.86,
            exchange="NSE",
            source="Mock",
        ),
        HoldingItem(
            ticker="TCS",
            isin="INE467B01029",
            company_name="Tata Consultancy Services Ltd",
            quantity=5,
            average_price=3650.0,
            last_price=3580.0,
            pnl=-350.0,
            pnl_percent=-1.92,
            exchange="NSE",
            source="Mock",
        ),
        HoldingItem(
            ticker="INFY",
            isin="INE009A01021",
            company_name="Infosys Ltd",
            quantity=20,
            average_price=1480.0,
            last_price=1520.0,
            pnl=800.0,
            pnl_percent=2.70,
            exchange="NSE",
            source="Mock",
        ),
        HoldingItem(
            ticker="HDFCBANK",
            isin="INE040A01034",
            company_name="HDFC Bank Ltd",
            quantity=8,
            average_price=1680.0,
            last_price=1650.0,
            pnl=-240.0,
            pnl_percent=-1.79,
            exchange="NSE",
            source="Mock",
        ),
    ]
    total_value = sum(h.last_price * h.quantity for h in holdings)
    return PortfolioState(
        holdings=holdings,
        total_value=round(total_value, 2),
        as_of_text="Mock portfolio (demo)",
    )

"""Shared data models for portfolio state and analysis output."""

from typing import Any

from pydantic import BaseModel, Field


class HoldingItem(BaseModel):
    """Single standardized holding across brokers."""

    ticker: str = Field(description="Trading symbol e.g. RELIANCE, TCS")
    isin: str = Field(default="", description="ISIN if available")
    company_name: str = Field(default="", description="Company name")
    quantity: int = Field(ge=0, description="Held quantity")
    average_price: float = Field(ge=0, description="Average cost price")
    last_price: float = Field(ge=0, description="Last / current price")
    pnl: float = Field(default=0, description="P&L in INR")
    pnl_percent: float = Field(default=0, description="P&L percentage")
    exchange: str = Field(default="NSE", description="Exchange code")
    source: str = Field(default="", description="Upstox or HDFC")


class PortfolioState(BaseModel):
    """Unified portfolio state consumed by agents."""

    holdings: list[HoldingItem] = Field(default_factory=list)
    total_value: float = Field(default=0, description="Total portfolio value at last price")
    as_of_text: str = Field(default="", description="Human-readable snapshot time")

    def tickers(self) -> list[str]:
        return [h.ticker for h in self.holdings]


class PersonaFeedback(BaseModel):
    """Per-ticker feedback from a single persona."""

    ticker: str
    persona: str
    feedback: str
    confidence_score: float = Field(ge=0, le=1, description="0-1 confidence")


class ConsensusRow(BaseModel):
    """One row for the dashboard: Ticker | Action | Persona Feedback | Confidence."""

    ticker: str
    action: str = Field(description="BUY | SELL | HOLD")
    persona_feedback: str = Field(description="Consolidated or Strategist feedback")
    confidence_score: float = Field(ge=0, le=1)


class ConsensusOutput(BaseModel):
    """Structured output from the Strategist / consensus run."""

    summary: str = Field(default="", description="Executive summary")
    ticker_actions: list[ConsensusRow] = Field(default_factory=list)
    raw_json: dict[str, Any] = Field(default_factory=dict)

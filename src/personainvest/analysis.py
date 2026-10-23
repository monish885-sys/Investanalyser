"""Orchestrate portfolio fetch and consensus analysis with error handling."""

import logging
from typing import Callable, Any

from personainvest.models import ConsensusOutput, PortfolioState
from personainvest.portfolio import get_portfolio_state
from personainvest.agents.crew import run_consensus_analysis

logger = logging.getLogger(__name__)


def run_analysis(
    use_mock: bool | None = None,
    stream_callback: Callable[[str], Any] | None = None,
) -> tuple[PortfolioState, ConsensusOutput]:
    """
    Load portfolio (mock or live), run consensus crew, return (portfolio_state, consensus_output).
    Handles API/rate-limit errors and returns safe defaults so the UI does not break.
    """
    try:
        state = get_portfolio_state(use_mock=use_mock)
    except Exception as e:
        logger.exception("Failed to load portfolio: %s", e)
        if stream_callback:
            stream_callback(f"Portfolio load error: {e}. Using empty portfolio.")
        state = PortfolioState(holdings=[], as_of_text="Error loading")

    if not state.holdings:
        return state, ConsensusOutput(
            summary="No holdings to analyze. Add positions or check API credentials.",
            ticker_actions=[],
            raw_json={},
        )

    try:
        consensus = run_consensus_analysis(state, stream_callback=stream_callback)
    except Exception as e:
        logger.exception("Consensus analysis failed: %s", e)
        if stream_callback:
            stream_callback(f"Analysis error: {e}")
        consensus = ConsensusOutput(
            summary=f"Analysis failed: {e}",
            ticker_actions=[],
            raw_json={},
        )

    return state, consensus

"""CrewAI crew: four personas (Portfolio Scout, News Sentinel, Earnings Whisperer, Strategist)."""

import json
import logging
import re
from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai_tools import TavilySearchTool

from personainvest.config import GEMINI_API_KEY, TAVILY_API_KEY
from personainvest.models import ConsensusOutput, ConsensusRow, PortfolioState

logger = logging.getLogger(__name__)

# Gemini 2.5 Flash (free tier has quota; 2.5 Pro free tier is often 0)
GEMINI_MODEL = "gemini/gemini-2.5-flash"


def _get_llm():
    """CrewAI LLM with Gemini; use env GEMINI_API_KEY or GOOGLE_API_KEY."""
    from crewai import LLM
    return LLM(
        model=GEMINI_MODEL,
        api_key=GEMINI_API_KEY or None,  # None => read from env
        temperature=0.2,
        max_tokens=8192,
    )


def _portfolio_context(state: PortfolioState) -> str:
    """Serialize portfolio for agent context."""
    lines = [
        f"Portfolio snapshot: {state.as_of_text}",
        f"Total value (INR): {state.total_value}",
        "Holdings:",
    ]
    for h in state.holdings:
        lines.append(
            f"  - {h.ticker} | {h.company_name or 'N/A'} | Qty: {h.quantity} | "
            f"Avg: {h.average_price} | LTP: {h.last_price} | P&L: {h.pnl} ({h.pnl_percent}%) | {h.source}"
        )
    return "\n".join(lines)


def create_crew(portfolio_context_str: str, tickers_str: str):
    """Build CrewAI crew with four agents and sequential tasks."""
    llm = _get_llm()
    tavily = TavilySearchTool(
        search_depth="advanced",
        max_results=5,
        topic="finance",
        time_range="month",
    ) if TAVILY_API_KEY else None

    # ---- Agents ----
    portfolio_scout = Agent(
        role="Portfolio Scout",
        goal="Fetch and clean portfolio data from brokers and produce a single, standardized portfolio summary for the team.",
        backstory="You are a meticulous data analyst who specializes in normalizing brokerage data. You ensure every holding has a clear ticker, quantity, cost, and current value so downstream analysts can focus on research.",
        llm=llm,
        tools=[],  # No web search; data is provided
        verbose=True,
    )

    news_sentinel = Agent(
        role="News Sentinel",
        goal="Find the latest Indian equity and macro news for the given tickers and summarize sentiment and key themes.",
        backstory="You are a financial news analyst focused on Indian markets. You use web search to find recent news, earnings hints, and macro trends that could impact these stocks.",
        llm=llm,
        tools=[tavily] if tavily else [],
        verbose=True,
    )

    earnings_whisperer = Agent(
        role="Earnings Whisperer",
        goal="Search for the latest earnings call transcripts, investor presentations, and management guidance for the given companies.",
        backstory="You are an expert at parsing earnings calls and investor materials. You look for management outlook, margin guidance, and capital allocation to inform the strategist.",
        llm=llm,
        tools=[tavily] if tavily else [],
        verbose=True,
    )

    strategist = Agent(
        role="Chief Investment Strategist (CIO)",
        goal="Produce a clear, actionable consensus: for each ticker give one of BUY, SELL, or HOLD, a short persona-based feedback line, and a confidence score (0-1). Include a 12-month outlook where relevant.",
        backstory="You are the CIO who synthesizes portfolio data, news sentiment, and earnings guidance into a single investment view. You output only valid JSON so the system can display it in a table.",
        llm=llm,
        tools=[],
        verbose=True,
    )

    # ---- Tasks ----
    scout_task = Task(
        description=f"Review and confirm the following portfolio. Produce a short summary listing each ticker and its weight/value. Do not change the data.\n\n{portfolio_context_str}",
        expected_output="A concise portfolio summary with ticker, quantity, value, and source.",
        agent=portfolio_scout,
    )

    news_task = Task(
        description=f"Search the web for the latest Indian market news and sentiment for these tickers: {tickers_str}. Focus on news from the last few weeks. Summarize sentiment (bullish/neutral/bearish) and any macro or sector themes.",
        expected_output="A brief report: for each ticker, 2-3 bullet points on recent news and overall sentiment.",
        agent=news_sentinel,
        context=[scout_task],
    )

    earnings_task = Task(
        description=f"Search for earnings call transcripts, investor presentations, or management guidance for: {tickers_str}. Prefer Indian listed companies. Summarize key guidance and outlook.",
        expected_output="A short summary per ticker: key management comments, margin/revenue outlook, and any risks mentioned.",
        agent=earnings_whisperer,
        context=[scout_task, news_task],
    )

    strategist_task = Task(
        description="""Using the portfolio summary, news sentiment, and earnings guidance, produce a consensus view.

Output MUST be a single valid JSON object with this exact structure (no markdown, no code fence):
{
  "summary": "One paragraph executive summary.",
  "ticker_actions": [
    {
      "ticker": "RELIANCE",
      "action": "BUY",
      "persona_feedback": "One line rationale from combined personas.",
      "confidence_score": 0.85
    }
  ]
}

Rules:
- action must be exactly one of: BUY, SELL, HOLD.
- confidence_score must be a number between 0 and 1.
- Include one entry per ticker from the portfolio.
- Keep persona_feedback to one short sentence.""",
        expected_output="A single JSON object with summary and ticker_actions array.",
        agent=strategist,
        context=[scout_task, news_task, earnings_task],
    )

    crew = Crew(
        agents=[portfolio_scout, news_sentinel, earnings_whisperer, strategist],
        tasks=[scout_task, news_task, earnings_task, strategist_task],
        process=Process.sequential,
        verbose=True,
    )
    return crew


def _parse_strategist_json(raw: str) -> ConsensusOutput:
    """Extract JSON from strategist output; handle markdown code blocks."""
    text = (raw or "").strip()
    # Try to find JSON block
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return ConsensusOutput(
            summary="Could not parse strategist output as JSON.",
            ticker_actions=[],
            raw_json={},
        )
    try:
        data = json.loads(match.group())
        summary = data.get("summary", "")
        rows = data.get("ticker_actions", [])
        ticker_actions = []
        allowed_actions = {"BUY", "SELL", "HOLD"}
        for r in rows:
            if isinstance(r, dict):
                action = str(r.get("action", "HOLD")).upper().strip()
                if action not in allowed_actions:
                    action = "HOLD"
                ticker_actions.append(ConsensusRow(
                    ticker=str(r.get("ticker", "")),
                    action=action,
                    persona_feedback=str(r.get("persona_feedback", "")),
                    confidence_score=min(1.0, max(0.0, float(r.get("confidence_score", 0.5)))),
                ))
        return ConsensusOutput(
            summary=summary,
            ticker_actions=ticker_actions,
            raw_json=data,
        )
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.warning("JSON parse error: %s", e)
        return ConsensusOutput(
            summary=f"Parse error: {e}",
            ticker_actions=[],
            raw_json={},
        )


def run_consensus_analysis(
    portfolio_state: PortfolioState,
    stream_callback: Any = None,
) -> ConsensusOutput:
    """
    Run the full crew and return structured ConsensusOutput.
    stream_callback: optional callable(message: str) for progress (e.g. Streamlit status).
    """
    ctx = _portfolio_context(portfolio_state)
    tickers_str = ", ".join(portfolio_state.tickers())
    if not tickers_str:
        return ConsensusOutput(
            summary="No holdings in portfolio.",
            ticker_actions=[],
            raw_json={},
        )

    crew = create_crew(ctx, tickers_str)
    if stream_callback:
        stream_callback("Kicking off crew: Portfolio Scout → News Sentinel → Earnings Whisperer → Strategist...")

    import time
    last_error = None
    for attempt in range(3):  # initial + 2 retries
        try:
            result = crew.kickoff()
            raw_output = result.raw if hasattr(result, "raw") else str(result)
            break
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                wait = 25  # seconds; API often says "retry in ~18s"
                if stream_callback:
                    stream_callback(f"Rate limited. Retrying in {wait}s (attempt {attempt + 1}/3)...")
                time.sleep(wait)
            else:
                logger.exception("Crew run failed: %s", e)
                if stream_callback:
                    stream_callback(f"Error: {e}")
                return ConsensusOutput(
                    summary=f"Crew run failed: {e}",
                    ticker_actions=[],
                    raw_json={},
                )
    else:
        logger.exception("Crew run failed after retries: %s", last_error)
        if stream_callback and last_error:
            stream_callback(f"Error: {last_error}")
        return ConsensusOutput(
            summary=f"Crew run failed (rate limit): {last_error}",
            ticker_actions=[],
            raw_json={},
        )

    if stream_callback:
        stream_callback("Parsing strategist JSON...")
    return _parse_strategist_json(raw_output)

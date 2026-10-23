# PersonaInvest

A **Python-based Multi-Agent Investment Analysis System** that fetches real-time portfolio data from Upstox and HDFC InvestRight, then runs an automated **consensus analysis** using Google Gemini across four investing personas.

## Features

- **Dual brokerage integration**: Upstox API v2 + HDFC Securities InvestRight Individual API
- **Mock data mode**: Test the app without live API credentials
- **Four AI personas** (CrewAI + Gemini 1.5 Pro):
  - **Portfolio Scout**: Fetches and standardizes holdings into a shared `PortfolioState`
  - **News Sentinel**: Uses Tavily to find Indian market news and sentiment
  - **Earnings Whisperer**: Searches earnings call transcripts and investor presentations
  - **Strategist (CIO)**: Consolidates inputs and outputs Buy/Sell/Hold with 12-month targets
- **Streamlit dashboard**: Dark theme, "Analyse My Portfolio" button, tabular results with confidence scores

## Setup

1. **Clone and enter project**
   ```bash
   cd Investanalyser
   ```

2. **Create virtual environment and install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set:
   - `UPSTOX_ACCESS_TOKEN` – from Upstox OAuth (or leave empty and use mock)
   - `HDFC_API_KEY` / `HDFC_API_SECRET` – from [HDFC Developer Portal](https://developer.hdfcsec.com/)
   - `GEMINI_API_KEY` – from [Google AI Studio](https://aistudio.google.com/apikey)
   - `TAVILY_API_KEY` – from [Tavily](https://app.tavily.com/)
   - `USE_MOCK_DATA=true` – to run without broker APIs

4. **Run the dashboard**
   ```bash
   streamlit run src/personainvest/app.py
   ```

## Project structure

```
Investanalyser/
├── .env.example
├── requirements.txt
├── README.md
└── src/
    └── personainvest/
        ├── __init__.py
        ├── config.py
        ├── models.py
        ├── clients/
        │   ├── __init__.py
        │   ├── upstox_client.py
        │   ├── hdfc_client.py
        │   └── mock_data.py
        ├── agents/
        │   ├── __init__.py
        │   └── crew.py
        ├── analysis.py
        └── app.py
```

## API keys

| Key | Purpose |
|-----|--------|
| `UPSTOX_ACCESS_TOKEN` | Upstox portfolio holdings |
| `HDFC_API_KEY` / `HDFC_API_SECRET` | HDFC InvestRight positions |
| `GEMINI_API_KEY` | CrewAI agents (Gemini 1.5 Pro) |
| `TAVILY_API_KEY` | Real-time news and transcript search |

## Disclaimer

This is for educational and research use. Not financial advice. Always verify data and decisions with your broker and advisor.

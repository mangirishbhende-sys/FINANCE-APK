# Bharat Pulse — Indian Stock Screener & Institutional Tracker

A single-file Streamlit dashboard (`app.py`) for Indian mid- and small-cap stocks:

1. **Fundamental Screener** — P/E, PEG, ROE, ROCE, debt/equity, ₹500 Cr–₹25,000 Cr market-cap band, with Screener.in links
2. **FII & DII Tracker** — latest institutional net cash flows and bullish/bearish sentiment
3. **Order Wins Feed** — Moneycontrol / Economic Times RSS filtered for large orders, contracts, and JVs
4. **Stock 360°** — pass/fail quality checklist plus Plotly price chart with 50- and 200-day moving averages

## Run on your computer

You only need Python 3.10+ and internet access.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

A browser window opens (usually http://localhost:8501).

**First load** of the screener can take a minute while Yahoo Finance data is downloaded. After that, results are cached for several hours. Use **Refresh live data** in the sidebar to force a new pull.

Missing Yahoo fields show as **N/A** instead of crashing the app.

This dashboard is for education and research, not investment advice.

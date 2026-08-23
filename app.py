"""
Bharat Pulse — Indian Mid/Small-Cap Screener & Institutional Tracker
A single-file Streamlit app for quality screening, FII/DII flows, order-win news, and a 360° stock checklist.
"""

from __future__ import annotations

import html
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

import feedparser
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf

# ---------------------------------------------------------------------------
# Page & theme
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Bharat Pulse · Stock Screener & Institutional Tracker",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,700;1,9..40,400&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

    :root {
        --bg: #070b14;
        --panel: #101827;
        --line: rgba(148, 163, 184, 0.16);
        --text: #e8eef9;
        --muted: #94a3b8;
        --gold: #f5c542;
        --teal: #2dd4bf;
        --blue: #60a5fa;
        --pass: #34d399;
        --fail: #fb7185;
    }

    html, body, [class*="css"] { font-family: "DM Sans", "IBM Plex Sans", sans-serif; }
    .stApp {
        background:
            radial-gradient(1200px 500px at 8% -10%, rgba(45, 212, 191, 0.10), transparent 50%),
            radial-gradient(900px 420px at 100% 0%, rgba(245, 197, 66, 0.08), transparent 45%),
            linear-gradient(180deg, #070b14 0%, #0b1220 100%);
        color: var(--text);
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c1424 0%, #0a101c 100%);
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] * { color: var(--text) !important; }

    .hero { padding: 0.2rem 0 1.2rem 0; border-bottom: 1px solid var(--line); margin-bottom: 1.25rem; }
    .eyebrow { color: var(--teal); letter-spacing: 0.18em; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; margin-bottom: 0.35rem; }
    .hero h1 { font-size: 2.05rem; font-weight: 700; letter-spacing: -0.03em; margin: 0; color: #f8fafc; }
    .hero p { color: var(--muted); margin: 0.45rem 0 0 0; font-size: 1.02rem; max-width: 760px; }

    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.9rem; margin: 0.4rem 0 1.1rem 0; }
    .kpi { background: linear-gradient(180deg, rgba(21,32,51,0.92), rgba(16,24,39,0.92)); border: 1px solid var(--line); border-radius: 16px; padding: 1.05rem 1.15rem; box-shadow: 0 10px 30px rgba(0,0,0,0.18); }
    .kpi .label { color: var(--muted); font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase; font-weight: 600; }
    .kpi .value { font-size: 1.7rem; font-weight: 700; margin-top: 0.25rem; letter-spacing: -0.03em; }
    .kpi .hint { color: var(--muted); font-size: 0.82rem; margin-top: 0.2rem; }
    .pos { color: var(--pass) !important; }
    .neg { color: var(--fail) !important; }
    .neu { color: var(--gold) !important; }

    .badge { display: inline-block; padding: 0.12rem 0.5rem; border-radius: 999px; font-size: 0.72rem; font-weight: 700; margin-right: 0.25rem; margin-bottom: 0.15rem; }
    .badge-pass { background: rgba(52, 211, 153, 0.16); color: #6ee7b7; border: 1px solid rgba(52,211,153,0.28); }
    .badge-fail { background: rgba(251, 113, 133, 0.14); color: #fda4af; border: 1px solid rgba(251,113,133,0.28); }
    .badge-na  { background: rgba(148, 163, 184, 0.12); color: #cbd5e1; border: 1px solid rgba(148,163,184,0.22); }

    .stock-card { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 0.95rem 1.05rem; margin-bottom: 0.75rem; }
    .stock-card h3 { margin: 0 0 0.15rem 0; font-size: 1.05rem; }
    .stock-card a { color: var(--blue); text-decoration: none; font-size: 0.82rem; }
    .meta { color: var(--muted); font-size: 0.84rem; }

    .check-row { display: flex; align-items: center; justify-content: space-between; background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 0.72rem 0.95rem; margin-bottom: 0.45rem; }
    .pill { border-radius: 999px; padding: 0.18rem 0.7rem; font-size: 0.78rem; font-weight: 700; }
    .pill-pass { background: rgba(52,211,153,0.15); color: #6ee7b7; }
    .pill-fail { background: rgba(251,113,133,0.15); color: #fda4af; }
    .pill-na { background: rgba(148,163,184,0.12); color: #cbd5e1; }

    .sentiment { border-radius: 18px; padding: 1.2rem 1.3rem; border: 1px solid var(--line); margin-bottom: 1rem; }
    .sentiment.bull { background: linear-gradient(135deg, rgba(16,185,129,0.16), rgba(16,24,39,0.6)); }
    .sentiment.bear { background: linear-gradient(135deg, rgba(244,63,94,0.16), rgba(16,24,39,0.6)); }
    .sentiment.flat { background: linear-gradient(135deg, rgba(245,197,66,0.12), rgba(16,24,39,0.6)); }

    div[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 0.35rem; border-bottom: 1px solid var(--line); }
    div[data-testid="stTabs"] [data-baseweb="tab"] { background: transparent; color: var(--muted); border-radius: 10px 10px 0 0; padding: 0.7rem 1rem; font-weight: 600; }
    div[data-testid="stTabs"] [aria-selected="true"] { color: #f8fafc !important; background: rgba(45, 212, 191, 0.08); border-bottom: 2px solid var(--teal); }
    [data-testid="stExpander"] { background: var(--panel); border: 1px solid var(--line); border-radius: 14px !important; margin-bottom: 0.45rem; }
    .footer-note { color: var(--muted); font-size: 0.78rem; margin-top: 1.5rem; padding-top: 0.8rem; border-top: 1px solid var(--line); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Strict screen defaults
# ---------------------------------------------------------------------------
MCAP_MIN_CR = 500.0
MCAP_MAX_CR = 25_000.0
PE_MAX = 25.0
PEG_MIN = 0.5
PEG_MAX = 1.0
ROE_MIN = 25.0
ROCE_MIN = 30.0
DE_MAX = 1.0
INR_PER_USD = 84.0

UNIVERSE: tuple[str, ...] = (
    "WAAREERTL.NS", "SWARAJENG.NS", "ECLERX.NS", "AFFLE.NS", "AJANTPHARM.NS",
    "APLAPOLLO.NS", "ASTRAL.NS", "AARTIIND.NS", "BATAINDIA.NS", "BHEL.NS",
    "BLUESTARCO.NS", "BSE.NS", "CAMS.NS", "CDSL.NS", "CESC.NS", "COFORGE.NS",
    "CREDITACC.NS", "CRISIL.NS", "CROMPTON.NS", "CUMMINSIND.NS", "CYIENT.NS",
    "DEEPAKNTR.NS", "DIXON.NS", "ELGIEQUIP.NS", "EMAMILTD.NS", "ENDURANCE.NS",
    "FINCABLES.NS", "FSL.NS", "GODFRYPHLP.NS", "GRINDWELL.NS", "GSPL.NS",
    "HAPPSTMNDS.NS", "HATSUN.NS", "HFCL.NS", "HINDCOPPER.NS", "HONAUT.NS",
    "IIFL.NS", "INDHOTEL.NS", "IPCALAB.NS", "ITI.NS", "JBCHEPHARM.NS",
    "JUBLFOOD.NS", "KAJARIACER.NS", "KALYANKJIL.NS", "KANSAINER.NS", "KEI.NS",
    "KPITTECH.NS", "LALPATHLAB.NS", "LAURUSLABS.NS", "LICHSGFIN.NS", "MAZDOCK.NS",
    "METROPOLIS.NS", "MINDACORP.NS", "NATCOPHARM.NS", "NAVINFLUOR.NS", "NH.NS",
    "NUVAMA.NS", "OFSS.NS", "PAGEIND.NS", "PERSISTENT.NS", "PHOENIXLTD.NS",
    "POLYCAB.NS", "POONAWALLA.NS", "RADICO.NS", "RAJESHEXPO.NS", "RATNAMANI.NS",
    "REDINGTON.NS", "ROUTE.NS", "SCHAEFFLER.NS", "SONACOMS.NS", "SUNTV.NS",
    "SUPREMEIND.NS", "SYNGENE.NS", "TATACHEM.NS", "TATAELXSI.NS", "THERMAX.NS",
    "TIMKEN.NS", "TRITURBINE.NS", "TVSMOTOR.NS", "UJJIVANSFB.NS", "VINATIORGA.NS",
    "VOLTAS.NS", "MANYAVAR.NS", "DEVYANI.NS", "CLEAN.NS", "FINEORG.NS",
    "GALAXYSURF.NS", "TANLA.NS", "INTELLECT.NS", "NEWGEN.NS", "LATENTVIEW.NS",
    "MASTEK.NS", "SONATSOFTW.NS", "ZENSARTECH.NS", "CENTURYPLY.NS", "CERA.NS",
    "SKFINDIA.NS", "ESABINDIA.NS", "AIAENG.NS", "GRINFRA.NS", "IRB.NS",
    "KNRCON.NS", "CAPLIPOINT.NS", "GLAND.NS", "ERIS.NS", "SUVENPHAR.NS",
    "GRANULES.NS",
)

ORDER_KEYWORDS = (
    "bags order",
    "wins contract",
    "receives order",
    "bagged",
    "wins order",
    "won a contract",
    "won contract",
    "jv",
    "joint venture",
    "export agreement",
    "order book",
    "secures order",
    "secures contract",
    "awarded contract",
    "purchase order",
)

RSS_FEEDS = (
    ("Moneycontrol", "https://www.moneycontrol.com/rss/latestnews.xml"),
    ("Moneycontrol Markets", "https://www.moneycontrol.com/rss/marketreports.xml"),
    ("Moneycontrol Business", "https://www.moneycontrol.com/rss/business.xml"),
    ("Economic Times Markets", "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
    ("Economic Times Corporate", "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms"),
    ("ET Stocks", "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms"),
    (
        "Google News (order wins)",
        "https://news.google.com/rss/search?q=%22bags+order%22+OR+%22wins+contract%22+OR+%22receives+order%22+OR+%22order+book%22+OR+%22export+agreement%22+when:7d&hl=en-IN&gl=IN&ceid=IN:en",
    ),
)

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ---------------------------------------------------------------------------
# Helpers — missing Yahoo fields become None / N/A, never a crash
# ---------------------------------------------------------------------------
def to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and pd.notna(value):
        if value != value:
            return None
        return float(value)
    try:
        text = str(value).strip().replace(",", "")
        if text in {"", "None", "nan", "NaN", "N/A", "-"}:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def fmt_num(value: Any, digits: int = 2, suffix: str = "") -> str:
    number = to_float(value)
    if number is None:
        return "N/A"
    return f"{number:,.{digits}f}{suffix}"


def nse_symbol(ticker: str) -> str:
    return ticker.replace(".NS", "").replace(".BO", "").strip().upper()


def screener_url(ticker: str) -> str:
    return f"https://www.screener.in/company/{nse_symbol(ticker)}/"


def normalize_ticker(raw: str) -> str:
    symbol = (raw or "").strip().upper()
    if not symbol:
        return ""
    if "." not in symbol:
        return f"{symbol}.NS"
    return symbol


def market_cap_cr(info: dict[str, Any]) -> float | None:
    cap = to_float(info.get("marketCap"))
    if cap is None:
        return None
    currency = str(info.get("currency") or info.get("financialCurrency") or "INR").upper()
    if currency == "USD":
        cap *= INR_PER_USD
    return cap / 1e7


def debt_to_equity_ratio(info: dict[str, Any]) -> float | None:
    raw = to_float(info.get("debtToEquity"))
    if raw is None:
        return None
    if abs(raw) > 5:
        return raw / 100.0
    return raw


def peg_ratio(info: dict[str, Any]) -> float | None:
    peg = to_float(info.get("pegRatio") or info.get("trailingPegRatio"))
    if peg is not None and peg > 0:
        return peg
    pe = to_float(info.get("trailingPE") or info.get("forwardPE"))
    growth = to_float(info.get("earningsGrowth") or info.get("earningsQuarterlyGrowth"))
    if pe is None or growth is None or growth <= 0:
        return None
    growth_pct = growth * 100.0 if abs(growth) <= 2 else growth
    if growth_pct <= 0:
        return None
    return pe / growth_pct


def statement_value(frame: pd.DataFrame | None, labels: tuple[str, ...]) -> float | None:
    if frame is None or getattr(frame, "empty", True):
        return None
    for label in labels:
        if label in frame.index:
            value = to_float(frame.loc[label].iloc[0])
            if value is not None:
                return value
    return None


def compute_roe_pct(ticker: yf.Ticker, info: dict[str, Any]) -> float | None:
    roe = to_float(info.get("returnOnEquity"))
    if roe is not None:
        return roe * 100.0 if abs(roe) <= 2 else roe
    try:
        net_income = statement_value(
            ticker.financials,
            ("Net Income", "Net Income Common Stockholders"),
        )
        equity = statement_value(
            ticker.balance_sheet,
            ("Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"),
        )
        if net_income is None or not equity:
            return None
        return (net_income / equity) * 100.0
    except Exception:
        return None


def compute_roce_pct(ticker: yf.Ticker, info: dict[str, Any]) -> float | None:
    for key in ("returnOnCapital", "returnOnCapitalEmployed"):
        raw = to_float(info.get(key))
        if raw is not None:
            return raw * 100.0 if abs(raw) <= 2 else raw
    try:
        ebit = statement_value(ticker.financials, ("EBIT", "Operating Income", "Ebit"))
        assets = statement_value(ticker.balance_sheet, ("Total Assets",))
        current_liab = statement_value(
            ticker.balance_sheet,
            ("Current Liabilities", "Total Current Liabilities"),
        )
        invested = statement_value(ticker.balance_sheet, ("Invested Capital",))
        capital = None
        if assets is not None and current_liab is not None:
            capital = assets - current_liab
        elif invested:
            capital = invested
        if ebit is None or not capital:
            return None
        return (ebit / capital) * 100.0
    except Exception:
        return None


def badge_html(label: str, value: float | None, passed: bool | None, suffix: str = "") -> str:
    if value is None or passed is None:
        klass = "badge-na"
    elif passed:
        klass = "badge-pass"
    else:
        klass = "badge-fail"
    shown = "N/A" if value is None else f"{value:.2f}{suffix}"
    return f'<span class="badge {klass}">{html.escape(label)} {html.escape(shown)}</span>'


def check_pe(pe: float | None, cap: float = PE_MAX) -> bool | None:
    if pe is None:
        return None
    return 0 < pe < cap


def check_peg(peg: float | None, lo: float = PEG_MIN, hi: float = PEG_MAX) -> bool | None:
    if peg is None:
        return None
    return lo <= peg <= hi


def check_roe(roe: float | None, floor: float = ROE_MIN) -> bool | None:
    if roe is None:
        return None
    return roe > floor


def check_roce(roce: float | None, floor: float = ROCE_MIN) -> bool | None:
    if roce is None:
        return None
    return roce > floor


def check_de(de: float | None, cap: float = DE_MAX) -> bool | None:
    if de is None:
        return None
    return 0 <= de < cap


def in_mcap_band(mcap_cr: float | None, lo: float = MCAP_MIN_CR, hi: float = MCAP_MAX_CR) -> bool | None:
    if mcap_cr is None:
        return None
    return lo <= mcap_cr <= hi


def headline_matches(title: str, summary: str) -> list[str]:
    blob = re.sub(r"<[^>]+>", " ", f"{title} {summary}").lower()
    hits: list[str] = []
    for key in ORDER_KEYWORDS:
        if len(key) <= 3:
            if re.search(rf"\b{re.escape(key)}\b", blob):
                hits.append(key)
        elif key in blob:
            hits.append(key)
    return hits


def detect_order_size(text: str) -> str:
    cleaned = html.unescape(re.sub(r"<[^>]+>", " ", text))
    patterns = (
        r"(?:₹|rs\.?|inr)\s*([\d,.]+)\s*(crore|cr|lakh|lac|billion|bn|million|mn)",
        r"([\d,.]+)\s*(crore|cr|lakh|lac)\s*(?:rupees|order|deal|contract)?",
        r"worth\s+(?:₹|rs\.?)?\s*([\d,.]+)\s*(crore|cr|lakh|lac|billion|million)",
    )
    for pattern in patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            return f"{match.group(1)} {match.group(2)}"
    return "N/A"


# ---------------------------------------------------------------------------
# Cached data fetchers
# ---------------------------------------------------------------------------
def safe_info(ticker: yf.Ticker) -> dict[str, Any]:
    try:
        info = ticker.info or {}
        if isinstance(info, dict) and info:
            return info
    except Exception:
        pass
    try:
        fast = getattr(ticker, "fast_info", None)
        if fast:
            return {
                "marketCap": getattr(fast, "market_cap", None),
                "currency": getattr(fast, "currency", None),
                "lastPrice": getattr(fast, "last_price", None),
            }
    except Exception:
        pass
    return {}


def fetch_fundamentals(symbol: str, include_roce: bool = True) -> dict[str, Any]:
    row: dict[str, Any] = {
        "ticker": symbol,
        "symbol": nse_symbol(symbol),
        "name": nse_symbol(symbol),
        "sector": "N/A",
        "mcap_cr": None,
        "pe": None,
        "peg": None,
        "roe": None,
        "roce": None,
        "de": None,
        "price": None,
        "screener": screener_url(symbol),
        "error": None,
    }
    try:
        stock = yf.Ticker(symbol)
        info = safe_info(stock)
        row["name"] = info.get("shortName") or info.get("longName") or nse_symbol(symbol)
        row["sector"] = info.get("sector") or "N/A"
        row["mcap_cr"] = market_cap_cr(info)
        row["pe"] = to_float(info.get("trailingPE") or info.get("forwardPE"))
        row["peg"] = peg_ratio(info)
        row["de"] = debt_to_equity_ratio(info)
        row["price"] = to_float(info.get("currentPrice") or info.get("regularMarketPrice"))
        row["roe"] = compute_roe_pct(stock, info) if include_roce else (
            (lambda r: None if r is None else (r * 100.0 if abs(r) <= 2 else r))(to_float(info.get("returnOnEquity")))
        )
        if include_roce:
            row["roce"] = compute_roce_pct(stock, info)
        else:
            for key in ("returnOnCapital", "returnOnCapitalEmployed"):
                raw = to_float(info.get(key))
                if raw is not None:
                    row["roce"] = raw * 100.0 if abs(raw) <= 2 else raw
                    break
    except Exception as exc:
        row["error"] = str(exc)
    return row


@st.cache_data(ttl=6 * 60 * 60, show_spinner=False)
def screen_universe(symbols: tuple[str, ...], compute_roce: bool = True) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    workers = min(12, max(4, len(symbols)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_fundamentals, sym, compute_roce): sym for sym in symbols}
        for future in as_completed(futures):
            try:
                rows.append(future.result())
            except Exception as exc:
                sym = futures[future]
                rows.append(
                    {
                        "ticker": sym,
                        "symbol": nse_symbol(sym),
                        "name": nse_symbol(sym),
                        "sector": "N/A",
                        "mcap_cr": None,
                        "pe": None,
                        "peg": None,
                        "roe": None,
                        "roce": None,
                        "de": None,
                        "price": None,
                        "screener": screener_url(sym),
                        "error": str(exc),
                    }
                )
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame = frame.sort_values(by=["mcap_cr"], ascending=False, na_position="last")
    return frame


@st.cache_data(ttl=30 * 60, show_spinner=False)
def fetch_fii_dii() -> dict[str, Any]:
    nse = fii_dii_from_nse()
    if nse is not None:
        return nse
    moneycontrol = fii_dii_from_moneycontrol()
    if moneycontrol is not None:
        return moneycontrol
    return {
        "ok": False,
        "error": "NSE API unavailable from this network · Moneycontrol table unavailable",
        "rows": [],
        "latest": None,
    }


def fii_dii_from_nse() -> dict[str, Any] | None:
    session = requests.Session()
    headers = {
        **HTTP_HEADERS,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.nseindia.com/reports/fii-dii",
    }
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=12)
        response = session.get("https://www.nseindia.com/api/fiidiiTradeReact", headers=headers, timeout=12)
        if response.status_code != 200:
            return None
        return normalize_nse_fiidii(response.json())
    except Exception:
        return None


def normalize_nse_fiidii(payload: Any) -> dict[str, Any] | None:
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = payload.get("data") or payload.get("fiiDii") or []
    else:
        return None
    if not records:
        return None

    by_date: dict[str, dict[str, Any]] = {}
    for item in records:
        category = str(item.get("category") or item.get("cat") or "").upper()
        date = str(item.get("date") or item.get("tradingDate") or "")
        buy = to_float(item.get("buyValue") or item.get("buyVal") or item.get("buy"))
        sell = to_float(item.get("sellValue") or item.get("sellVal") or item.get("sell"))
        net = to_float(item.get("netValue") or item.get("netVal") or item.get("net"))
        if net is None and buy is not None and sell is not None:
            net = buy - sell
        kind = "FII" if ("FII" in category or "FPI" in category) else "DII" if "DII" in category else category
        bucket = by_date.setdefault(date, {"date": date, "fii_net": None, "dii_net": None})
        if kind == "FII":
            bucket["fii_net"] = net
            bucket["fii_buy"] = buy
            bucket["fii_sell"] = sell
        elif kind == "DII":
            bucket["dii_net"] = net
            bucket["dii_buy"] = buy
            bucket["dii_sell"] = sell

    rows = list(by_date.values())
    if not rows:
        return None
    return {"ok": True, "source": "NSE", "rows": rows, "latest": rows[0]}


def fii_dii_from_moneycontrol() -> dict[str, Any] | None:
    urls = (
        "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php",
        "https://www.moneycontrol.com/india/stockmarket/fii-dii-activity/marketstatistics/nse/cash.html",
    )
    for url in urls:
        tables: list[pd.DataFrame] = []
        try:
            tables = pd.read_html(url, flavor="lxml")
        except Exception:
            try:
                html_text = requests.get(url, headers=HTTP_HEADERS, timeout=15).text
                tables = pd.read_html(html_text, flavor="lxml")
            except Exception:
                continue
        for table in tables:
            blob = " ".join(str(c).lower() for c in table.columns)
            if "fii" not in blob and "dii" not in blob:
                latest = extract_mc_from_rows(table)
            else:
                latest = extract_mc_from_rows(table)
            if latest:
                return {"ok": True, "source": "Moneycontrol", "rows": [latest], "latest": latest}
    return None


def extract_mc_from_rows(frame: pd.DataFrame) -> dict[str, Any] | None:
    if frame.empty:
        return None
    fii_net = dii_net = fii_buy = fii_sell = dii_buy = dii_sell = None
    date_val = None
    for _, row in frame.head(10).iterrows():
        joined = " ".join(str(v) for v in row.values).upper()
        nums = [n for n in (to_float(v) for v in row.values) if n is not None]
        if "FII" in joined or "FPI" in joined:
            if len(nums) >= 3:
                fii_buy, fii_sell, fii_net = nums[0], nums[1], nums[2]
            elif nums:
                fii_net = nums[-1]
        if "DII" in joined:
            if len(nums) >= 3:
                dii_buy, dii_sell, dii_net = nums[0], nums[1], nums[2]
            elif nums:
                dii_net = nums[-1]
        if date_val is None:
            for val in row.values:
                text = str(val)
                if re.search(r"\d{1,2}[-/]\w{3}[-/]\d{2,4}|\d{4}-\d{2}-\d{2}", text):
                    date_val = text
                    break
    if fii_net is None and dii_net is None:
        return None
    return {
        "date": date_val or "Latest session",
        "fii_net": fii_net,
        "dii_net": dii_net,
        "fii_buy": fii_buy,
        "fii_sell": fii_sell,
        "dii_buy": dii_buy,
        "dii_sell": dii_sell,
    }


@st.cache_data(ttl=20 * 60, show_spinner=False)
def fetch_order_wins() -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source, url in RSS_FEEDS:
        try:
            parsed = feedparser.parse(url)
        except Exception:
            continue
        for entry in parsed.entries[:50]:
            title = (entry.get("title") or "").strip()
            summary = entry.get("summary") or entry.get("description") or ""
            matched = headline_matches(title, summary)
            if not matched:
                continue
            key = re.sub(r"\s+", " ", title.lower())
            if key in seen:
                continue
            seen.add(key)
            published = entry.get("published") or entry.get("updated") or ""
            ts = None
            for attr in ("published_parsed", "updated_parsed"):
                parsed_ts = entry.get(attr)
                if parsed_ts:
                    try:
                        ts = datetime(*parsed_ts[:6], tzinfo=timezone.utc)
                    except Exception:
                        ts = None
            alerts.append(
                {
                    "title": title,
                    "source": source,
                    "link": entry.get("link") or url,
                    "published": published,
                    "timestamp": ts.isoformat() if ts else published or "N/A",
                    "sort_ts": ts.timestamp() if ts else 0.0,
                    "summary": re.sub(r"<[^>]+>", " ", str(summary)).strip(),
                    "order_size": detect_order_size(f"{title} {summary}"),
                    "matched": matched,
                }
            )
    alerts.sort(key=lambda item: item["sort_ts"], reverse=True)
    return alerts[:60]


@st.cache_data(ttl=30 * 60, show_spinner=False)
def fetch_price_history(symbol: str, period: str = "2y") -> pd.DataFrame:
    try:
        history = yf.download(
            symbol,
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
        )
    except Exception:
        return pd.DataFrame()
    if history is None or history.empty:
        return pd.DataFrame()
    if isinstance(history.columns, pd.MultiIndex):
        history.columns = [col[0] for col in history.columns]
    history = history.rename(columns=str.title)
    if "Close" not in history.columns:
        return pd.DataFrame()
    history["MA50"] = history["Close"].rolling(50).mean()
    history["MA200"] = history["Close"].rolling(200).mean()
    return history


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
def render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">Bharat Pulse · NSE Mid & Small Caps</div>
            <h1>Stock Screener & Institutional Tracker</h1>
            <p>
                Quality-first fundamental screen, live FII/DII cash flows, corporate order-win alerts,
                and a 360° single-stock checklist — built for Indian public markets.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_screen(
    frame: pd.DataFrame,
    pe_max: float,
    peg_lo: float,
    peg_hi: float,
    roe_min: float,
    roce_min: float,
    de_max: float,
    mcap_lo: float,
    mcap_hi: float,
    require_all: bool,
) -> pd.DataFrame:
    if frame.empty:
        return frame
    work = frame.copy()
    work["pass_mcap"] = work["mcap_cr"].map(lambda v: in_mcap_band(v, mcap_lo, mcap_hi))
    work["pass_pe"] = work["pe"].map(lambda v: check_pe(v, pe_max))
    work["pass_peg"] = work["peg"].map(lambda v: check_peg(v, peg_lo, peg_hi))
    work["pass_roe"] = work["roe"].map(lambda v: check_roe(v, roe_min))
    work["pass_roce"] = work["roce"].map(lambda v: check_roce(v, roce_min))
    work["pass_de"] = work["de"].map(lambda v: check_de(v, de_max))
    flags = ["pass_mcap", "pass_pe", "pass_peg", "pass_roe", "pass_roce", "pass_de"]
    work["passes"] = work[flags].apply(lambda r: sum(1 for x in r if x is True), axis=1)
    work["all_pass"] = work[flags].apply(lambda r: all(x is True for x in r), axis=1)
    if require_all:
        return work[work["all_pass"]]
    return work[work["pass_mcap"] != False]  # noqa: E712


def color_by_flag(series: pd.Series, flags: list[Any]) -> list[str]:
    styles = []
    for i, _ in enumerate(series):
        flag = flags[i] if i < len(flags) else None
        if flag is True:
            styles.append("background-color: rgba(52,211,153,0.18); color: #d1fae5;")
        elif flag is False:
            styles.append("background-color: rgba(251,113,133,0.16); color: #ffe4e6;")
        else:
            styles.append("background-color: rgba(148,163,184,0.10); color: #e2e8f0;")
    return styles


def render_screener(frame: pd.DataFrame, require_all: bool) -> None:
    st.subheader("Fundamental Screener")
    st.caption(
        "Universe: Indian mid-cap & small-cap names with market cap ₹500 Cr – ₹25,000 Cr. "
        "Strict quality: P/E < 25, PEG 0.5–1.0, ROE > 25%, ROCE > 30%, Debt/Equity < 1.0."
    )
    if frame.empty:
        st.warning("No stocks to show. Relax a sidebar filter, switch off strict mode, or click Refresh live data.")
        return

    search = st.text_input("Filter by name, ticker, or sector", placeholder="e.g. ECLERX, engineering, chemicals")
    view = frame.reset_index(drop=True)
    if search.strip():
        query = search.strip().lower()
        view = view[
            view["symbol"].str.lower().str.contains(query, na=False)
            | view["name"].str.lower().str.contains(query, na=False)
            | view["sector"].str.lower().str.contains(query, na=False)
        ].reset_index(drop=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Names in this view", f"{len(view)}")
    c2.metric("Rows after search", f"{len(view)}")
    c3.metric("Full-criteria passes", f"{int(frame['all_pass'].sum()) if 'all_pass' in frame else 0}")
    c4.metric("Mode", "Strict" if require_all else "Universe + badges")

    if view.empty:
        st.info("No stocks match the current search. Clear the box or relax a threshold.")
        return

    table = pd.DataFrame(
        {
            "Ticker": view["symbol"],
            "Company": view["name"],
            "Sector": view["sector"],
            "Price (₹)": view["price"].map(lambda v: None if v is None else round(float(v), 2)),
            "MCap (₹ Cr)": view["mcap_cr"].map(lambda v: None if v is None else round(float(v), 1)),
            "P/E": view["pe"].map(lambda v: None if v is None else round(float(v), 2)),
            "PEG": view["peg"].map(lambda v: None if v is None else round(float(v), 2)),
            "ROE %": view["roe"].map(lambda v: None if v is None else round(float(v), 2)),
            "ROCE %": view["roce"].map(lambda v: None if v is None else round(float(v), 2)),
            "D/E": view["de"].map(lambda v: None if v is None else round(float(v), 2)),
            "Passed": view["passes"],
            "Screener.in": view["screener"],
        }
    )
    styler = (
        table.style.hide(axis="index")
        .apply(lambda s: color_by_flag(s, view["pass_pe"].tolist()), subset=["P/E"])
        .apply(lambda s: color_by_flag(s, view["pass_peg"].tolist()), subset=["PEG"])
        .apply(lambda s: color_by_flag(s, view["pass_roe"].tolist()), subset=["ROE %"])
        .apply(lambda s: color_by_flag(s, view["pass_roce"].tolist()), subset=["ROCE %"])
        .apply(lambda s: color_by_flag(s, view["pass_de"].tolist()), subset=["D/E"])
        .format(
            {
                "Price (₹)": lambda v: "N/A" if pd.isna(v) else f"{v:,.2f}",
                "MCap (₹ Cr)": lambda v: "N/A" if pd.isna(v) else f"{v:,.1f}",
                "P/E": lambda v: "N/A" if pd.isna(v) else f"{v:.2f}",
                "PEG": lambda v: "N/A" if pd.isna(v) else f"{v:.2f}",
                "ROE %": lambda v: "N/A" if pd.isna(v) else f"{v:.2f}",
                "ROCE %": lambda v: "N/A" if pd.isna(v) else f"{v:.2f}",
                "D/E": lambda v: "N/A" if pd.isna(v) else f"{v:.2f}",
            }
        )
    )
    st.dataframe(
        styler,
        width="stretch",
        height=min(640, 80 + 28 * min(len(table), 18)),
        column_config={"Screener.in": st.column_config.LinkColumn("Screener.in")},
    )

    st.markdown("##### Passing metric badges")
    st.caption("Green = pass · Rose = fail · Grey = N/A (Yahoo did not publish that field)")
    for _, row in view.head(12).iterrows():
        badges = "".join(
            [
                badge_html("P/E", row["pe"], row["pass_pe"]),
                badge_html("PEG", row["peg"], row["pass_peg"]),
                badge_html("ROE", row["roe"], row["pass_roe"], "%"),
                badge_html("ROCE", row["roce"], row["pass_roce"], "%"),
                badge_html("D/E", row["de"], row["pass_de"]),
                badge_html("MCap ₹Cr", row["mcap_cr"], row["pass_mcap"]),
            ]
        )
        st.markdown(
            f"""
            <div class="stock-card">
                <h3>{html.escape(str(row["name"]))} · {html.escape(str(row["symbol"]))}</h3>
                <div class="meta">{html.escape(str(row["sector"]))} · Price {fmt_num(row["price"])} ·
                <a href="{html.escape(row["screener"])}" target="_blank" rel="noopener">Open on Screener.in ↗</a></div>
                <div style="margin-top:0.55rem;">{badges}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_institutional(data: dict[str, Any]) -> None:
    st.subheader("Live Institutional Activity — FII & DII")
    st.caption("Cash-market net flows in ₹ crore. Sentiment is bullish when combined FII+DII net is positive.")

    if not data.get("ok") or not data.get("latest"):
        st.error(
            "Could not fetch live FII/DII numbers right now "
            f"({data.get('error') or 'no source responded'}). "
            "NSE sometimes blocks datacenter IPs — retry in a few minutes."
        )
        return

    latest = data["latest"]
    fii = to_float(latest.get("fii_net"))
    dii = to_float(latest.get("dii_net"))
    combined = None if fii is None and dii is None else (fii or 0.0) + (dii or 0.0)
    date_lbl = latest.get("date") or "Latest session"

    if combined is None:
        label, cls = "Insufficient data", "flat"
    elif combined > 0:
        label, cls = "Net Positive · Bullish institutional sentiment", "bull"
    elif combined < 0:
        label, cls = "Net Negative · Bearish institutional sentiment", "bear"
    else:
        label, cls = "Neutral · Institutions flat on the day", "flat"

    st.markdown(
        f"""
        <div class="sentiment {cls}">
            <div class="eyebrow">Cash market · {html.escape(str(date_lbl))} · Source {html.escape(str(data.get("source", "—")))}</div>
            <h2 style="margin:0.2rem 0 0.35rem 0;">{html.escape(label)}</h2>
            <div class="meta">Combined net (FII + DII): <b>{fmt_num(combined, 2)} Cr</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    fii_cls = "pos" if (fii or 0) > 0 else "neg" if (fii or 0) < 0 else "neu"
    dii_cls = "pos" if (dii or 0) > 0 else "neg" if (dii or 0) < 0 else "neu"
    comb_cls = "pos" if (combined or 0) > 0 else "neg" if (combined or 0) < 0 else "neu"
    st.markdown(
        f"""
        <div class="kpi-grid">
            <div class="kpi">
                <div class="label">FII / FPI Net</div>
                <div class="value {fii_cls}">{'Buy' if (fii or 0) > 0 else 'Sell' if (fii or 0) < 0 else 'Flat'} {fmt_num(abs(fii) if fii is not None else None, 2)} Cr</div>
                <div class="hint">Buy {fmt_num(latest.get("fii_buy"))} · Sell {fmt_num(latest.get("fii_sell"))}</div>
            </div>
            <div class="kpi">
                <div class="label">DII Net</div>
                <div class="value {dii_cls}">{'Buy' if (dii or 0) > 0 else 'Sell' if (dii or 0) < 0 else 'Flat'} {fmt_num(abs(dii) if dii is not None else None, 2)} Cr</div>
                <div class="hint">Buy {fmt_num(latest.get("dii_buy"))} · Sell {fmt_num(latest.get("dii_sell"))}</div>
            </div>
            <div class="kpi">
                <div class="label">Combined institutions</div>
                <div class="value {comb_cls}">{fmt_num(combined, 2)} Cr</div>
                <div class="hint">FII often leads foreign risk appetite; DIIs often absorb supply.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    hist = pd.DataFrame(data.get("rows") or [])
    if hist.empty:
        return
    show_cols = [c for c in ("date", "fii_net", "dii_net", "fii_buy", "fii_sell", "dii_buy", "dii_sell") if c in hist.columns]
    pretty = hist[show_cols].rename(
        columns={
            "date": "Date",
            "fii_net": "FII Net (₹ Cr)",
            "dii_net": "DII Net (₹ Cr)",
            "fii_buy": "FII Buy",
            "fii_sell": "FII Sell",
            "dii_buy": "DII Buy",
            "dii_sell": "DII Sell",
        }
    )
    st.dataframe(pretty, width="stretch", hide_index=True)
    if "fii_net" in hist.columns and len(hist) > 1:
        chart = go.Figure()
        chart.add_bar(x=hist["date"], y=hist["fii_net"], name="FII Net", marker_color="#60a5fa")
        chart.add_bar(x=hist["date"], y=hist["dii_net"], name="DII Net", marker_color="#2dd4bf")
        chart.update_layout(
            barmode="group",
            template="plotly_dark",
            height=340,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h"),
            margin=dict(l=10, r=10, t=30, b=10),
            yaxis_title="₹ Crore",
        )
        st.plotly_chart(chart, width="stretch")


def render_orders(alerts: list[dict[str, Any]]) -> None:
    st.subheader("Huge Orders & Major Corporate Wins")
    st.caption(
        "Headlines from Moneycontrol and Economic Times RSS (plus a Google News backup), "
        "filtered for order wins, contracts, JVs, export agreements, and order-book updates."
    )
    if not alerts:
        st.info("No matching order-win headlines in the latest feed pull. Try Refresh after market hours.")
        return

    query = st.text_input("Search alerts", placeholder="e.g. defence, railway, export, L&T")
    filtered = alerts
    if query.strip():
        q = query.strip().lower()
        filtered = [a for a in alerts if q in a["title"].lower() or q in (a.get("summary") or "").lower()]

    st.markdown(f"**{len(filtered)}** alerts after keyword filter.")
    for alert in filtered:
        with st.expander(alert["title"], expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Timestamp**  \n{alert.get('timestamp') or 'N/A'}")
            c2.markdown(f"**Order size detected**  \n{alert.get('order_size') or 'N/A'}")
            c3.markdown(f"**Source**  \n{alert.get('source') or 'N/A'}")
            if alert.get("summary"):
                st.write(alert["summary"][:800])
            matched = ", ".join(alert.get("matched") or [])
            if matched:
                st.caption(f"Matched keywords: {matched}")
            if alert.get("link"):
                st.markdown(f"[Open original article ↗]({alert['link']})")


def checklist_row(title: str, detail: str, status: bool | None) -> None:
    if status is True:
        pill, klass = "PASS", "pill-pass"
    elif status is False:
        pill, klass = "FAIL", "pill-fail"
    else:
        pill, klass = "N/A", "pill-na"
    st.markdown(
        f"""
        <div class="check-row">
            <div>
                <div style="font-weight:700;">{html.escape(title)}</div>
                <div class="meta">{html.escape(detail)}</div>
            </div>
            <div class="pill {klass}">{pill}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stock_360(default_ticker: str) -> None:
    st.subheader("Single Stock 360° Checklist")
    st.caption("Search any NSE ticker (`.NS` is added automatically). Checklist uses the same quality gates as the screener.")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        raw = st.text_input(
            "Ticker",
            value=default_ticker,
            placeholder="WAAREERTL.NS  ·  SWARAJENG.NS  ·  ECLERX.NS",
        )
    with col_b:
        period = st.selectbox("Chart window", ["6mo", "1y", "2y", "5y", "max"], index=2)

    symbol = normalize_ticker(raw)
    if not symbol:
        st.info("Enter a ticker to load the 360° view.")
        return

    with st.spinner(f"Loading {symbol}…"):
        fund_frame = screen_universe((symbol,), compute_roce=True)
        fund = fund_frame.iloc[0].to_dict() if not fund_frame.empty else fetch_fundamentals(symbol, include_roce=True)
        history = fetch_price_history(symbol, period=period)

    name = fund.get("name") or nse_symbol(symbol)
    st.markdown(
        f"""
        <div class="stock-card">
            <h3>{html.escape(str(name))} · {html.escape(nse_symbol(symbol))}</h3>
            <div class="meta">
                {html.escape(str(fund.get("sector") or "N/A"))} · Last price {fmt_num(fund.get("price"))} ·
                MCap {fmt_num(fund.get("mcap_cr"), 1)} Cr ·
                <a href="{html.escape(screener_url(symbol))}" target="_blank" rel="noopener">Screener.in ↗</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    checks = [
        ("P/E < 25", f"Trailing P/E = {fmt_num(fund.get('pe'))}", check_pe(fund.get("pe"))),
        ("PEG 0.5 – 1.0", f"PEG = {fmt_num(fund.get('peg'))}", check_peg(fund.get("peg"))),
        ("ROE > 25%", f"ROE = {fmt_num(fund.get('roe'))}%", check_roe(fund.get("roe"))),
        ("ROCE > 30%", f"ROCE = {fmt_num(fund.get('roce'))}%", check_roce(fund.get("roce"))),
        ("Debt/Equity < 1.0", f"D/E = {fmt_num(fund.get('de'))}x", check_de(fund.get("de"))),
        (
            "Mid/Small cap band",
            f"Market cap = {fmt_num(fund.get('mcap_cr'), 1)} Cr (₹500–25,000 Cr)",
            in_mcap_band(fund.get("mcap_cr")),
        ),
    ]
    passed = sum(1 for *_, status in checks if status is True)
    st.markdown(f"**{passed} / {len(checks)}** gates passed (missing Yahoo fields count as N/A, not fail).")
    for title, detail, status in checks:
        checklist_row(title, detail, status)

    if history.empty:
        st.warning("Price history is unavailable for this ticker (N/A).")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=history.index, y=history["Close"], name="Close", line=dict(color="#e8eef9", width=2)))
    fig.add_trace(go.Scatter(x=history.index, y=history["MA50"], name="50-day MA", line=dict(color="#2dd4bf", width=1.6)))
    fig.add_trace(go.Scatter(x=history.index, y=history["MA200"], name="200-day MA", line=dict(color="#f5c542", width=1.6)))
    fig.update_layout(
        template="plotly_dark",
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=10, r=10, t=40, b=10),
        yaxis_title="Price (₹)",
        title=f"{nse_symbol(symbol)} — price with 50 & 200 DMA",
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148,163,184,0.12)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(148,163,184,0.12)")
    st.plotly_chart(fig, width="stretch")

    last_close = to_float(history["Close"].iloc[-1])
    ma50 = to_float(history["MA50"].iloc[-1])
    ma200 = to_float(history["MA200"].iloc[-1])
    c1, c2, c3 = st.columns(3)
    c1.metric("Last close", fmt_num(last_close))
    c2.metric("50-day MA", fmt_num(ma50))
    c3.metric("200-day MA", fmt_num(ma200))
    if ma50 is not None and ma200 is not None:
        if ma50 > ma200:
            st.success("50-day MA is above the 200-day MA (golden-cross style trend support).")
        else:
            st.warning("50-day MA is below the 200-day MA (longer-term trend is still weak).")


def main() -> None:
    render_hero()

    with st.sidebar:
        st.markdown("### Controls")
        st.caption("Defaults match the strict mid/small-cap quality screen. Tweak only if you know why.")
        pe_max = st.slider("Max P/E", 5.0, 60.0, PE_MAX, 0.5)
        peg_lo, peg_hi = st.slider("PEG range", 0.0, 3.0, (PEG_MIN, PEG_MAX), 0.05)
        roe_min = st.slider("Min ROE %", 0.0, 50.0, ROE_MIN, 0.5)
        roce_min = st.slider("Min ROCE %", 0.0, 60.0, ROCE_MIN, 0.5)
        de_max = st.slider("Max Debt/Equity", 0.0, 3.0, DE_MAX, 0.05)
        mcap_lo, mcap_hi = st.slider("Market cap band (₹ Cr)", 100.0, 50_000.0, (MCAP_MIN_CR, MCAP_MAX_CR), 100.0)
        require_all = st.toggle("Strict mode (all filters must pass)", value=True)
        compute_roce = st.toggle("Compute ROE/ROCE from financial statements", value=True)
        extra = st.text_input("Add tickers to universe", placeholder="ROUTE.NS, TANLA, NEWGEN")
        default_360 = st.text_input("Default 360° ticker", value="ECLERX.NS")
        if st.button("Refresh live data", width="stretch"):
            st.cache_data.clear()
            st.rerun()
        st.markdown("---")
        st.caption(
            "Fundamentals: Yahoo Finance via yfinance. "
            "Institutional flows: NSE (Moneycontrol fallback). "
            "Order alerts: Moneycontrol & Economic Times RSS. "
            "Missing fields render as N/A."
        )

    extra_syms = [normalize_ticker(part) for part in re.split(r"[,\s]+", extra) if part.strip()] if extra.strip() else []
    symbols = tuple(dict.fromkeys([*UNIVERSE, *extra_syms]))

    tab_screen, tab_fii, tab_orders, tab_360 = st.tabs(
        ["① Fundamental Screener", "② FII & DII Tracker", "③ Order Wins Feed", "④ Stock 360°"]
    )

    with tab_screen:
        with st.spinner("Screening mid & small caps from Yahoo Finance. First run can take a minute…"):
            raw = screen_universe(symbols, compute_roce=compute_roce)
        screened = apply_screen(
            raw,
            pe_max=pe_max,
            peg_lo=peg_lo,
            peg_hi=peg_hi,
            roe_min=roe_min,
            roce_min=roce_min,
            de_max=de_max,
            mcap_lo=mcap_lo,
            mcap_hi=mcap_hi,
            require_all=require_all,
        )
        render_screener(screened, require_all=require_all)

    with tab_fii:
        with st.spinner("Fetching latest FII / DII cash flows…"):
            flows = fetch_fii_dii()
        render_institutional(flows)

    with tab_orders:
        with st.spinner("Pulling Moneycontrol & Economic Times order-win headlines…"):
            alerts = fetch_order_wins()
        render_orders(alerts)

    with tab_360:
        render_stock_360(default_360)

    st.markdown(
        """
        <div class="footer-note">
            Educational market dashboard — not investment advice. Yahoo Finance, NSE and news RSS fields can lag or be incomplete.
            Always cross-check filings and Screener.in before acting.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

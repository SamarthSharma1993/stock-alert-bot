import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ================= TELEGRAM =================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def send_msg(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ================= CONFIG =================
TICKERS = ["META", "AMZN", "AAPL", "MSFT", "GOOGL", "NVDA", "NFLX", "MELI", "QQQ"]
API_KEY = os.environ["TIINGO_API_KEY"]

END_DATE = datetime.today().date()
START_DATE = END_DATE - timedelta(days=3*365)

# ================= FUNDAMENTAL SCORE =================
FUNDAMENTAL_SCORE = {
    "NVDA": 9,
    "MSFT": 9,
    "META": 9,
    "AMZN": 8,
    "GOOGL": 8,
    "MELI": 8,
    "AAPL": 6,
    "NFLX": 6,
    "QQQ": 8
}

AI_LEADERS = ["NVDA", "MSFT", "AMZN", "META"]

# ================= RSI =================
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ================= FETCH =================
def fetch_data(ticker):
    url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices"
    params = {
        "startDate": START_DATE.isoformat(),
        "endDate": END_DATE.isoformat(),
        "token": API_KEY
    }

    r = requests.get(url, params=params)
    r.raise_for_status()

    df = pd.DataFrame(r.json())
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    df.sort_index(inplace=True)

    return df

# ================= SIGNAL ENGINE =================
def generate_signal(df, ticker):
    df["50DMA"] = df["close"].rolling(50).mean()
    df["200DMA"] = df["close"].rolling(200).mean()
    df["RSI"] = compute_rsi(df["close"])
    df["RET_20"] = df["close"].pct_change(20)

    df = df.dropna()
    latest = df.iloc[-1]

    price = latest["close"]
    dma50 = latest["50DMA"]
    dma200 = latest["200DMA"]
    rsi = latest["RSI"]
    ret20 = latest["RET_20"]

    fundamental = FUNDAMENTAL_SCORE.get(ticker, 5)

    # ================= TREND DETECTION =================
    strong_trend = price > dma50 > dma200
    weak_trend = price < dma200

    # ================= MOMENTUM =================
    strong_momentum = ret20 > 0.08  # 8% in 20 days
    mild_momentum = ret20 > 0.03

    # ================= SIGNAL LOGIC =================

    # 🚀 STRONG BUY
    if (
        strong_trend and
        strong_momentum and
        rsi > 55 and
        fundamental >= 8
    ):
        return "🔥 STRONG BUY"

    # 🟢 BUY (Pullback in uptrend)
    if (
        price < dma50 and price > dma200 and
        40 < rsi < 60 and
        fundamental >= 7
    ):
        return "🟢 BUY"

    # 🟢 BUY (AI leader accumulation)
    if (
        ticker in AI_LEADERS and
        strong_trend and
        rsi > 50
    ):
        return "🟢 BUY"

    # ⚠️ AVOID (downtrend + weak fundamentals)
    if weak_trend and fundamental <= 6:
        return "⚠️ AVOID"

    # Default
    return "HOLD"

# ================= RUN =================
messages = []

for ticker in TICKERS:
    try:
        df = fetch_data(ticker)
        signal = generate_signal(df, ticker)
        price = round(df.iloc[-1]["close"], 2)

        messages.append(f"{ticker} → {signal} | ${price}")

    except Exception as e:
        messages.append(f"{ticker} → ERROR: {str(e)}")

# ================= FINAL MESSAGE =================
final_msg = "📊 Smart Stock Signals\n\n" + "\n".join(messages)

send_msg(final_msg)

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
TICKERS = ["NVDA", "MSFT", "GOOGL", "AMZN", "META", "TSM", "AVGO"]

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
    "TSM": 9,
    "AVGO": 9
}

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

# ================= ALLOCATION ENGINE =================
def generate_signal(df, ticker):

    df["200DMA"] = df["close"].rolling(200).mean()
    df["RSI"] = compute_rsi(df["close"])

    df = df.dropna()
    latest = df.iloc[-1]

    price = latest["close"]
    dma200 = latest["200DMA"]
    rsi = latest["RSI"]

    fundamental = FUNDAMENTAL_SCORE.get(ticker, 5)

    # Distance from 200DMA
    dist = (price - dma200) / dma200

    # ================= SCORE =================
    score = 0

    if dist < -0.15:
        score += 5
    elif dist < -0.08:
        score += 3
    elif dist < -0.03:
        score += 2
    else:
        score += 1

    if rsi < 35:
        score += 3
    elif rsi < 45:
        score += 2

    score *= (fundamental / 10)

    # Normalize to %
    allocation = min(round(score / 8 * 100), 100)

    # ================= LABEL =================
    if allocation >= 70:
        label = "🔥 STRONG BUY"
    elif allocation >= 50:
        label = "🟢 BUY"
    elif allocation >= 20:
        label = "🟡 ACCUMULATE"
    elif allocation > 0:
        label = "HOLD"
    else:
        label = "❌ SKIP"

    return label, allocation, round(price, 2), round(dist * 100, 2)

# ================= RUN =================
messages = []

for ticker in TICKERS:
    try:
        df = fetch_data(ticker)
        label, allocation, price, dist = generate_signal(df, ticker)

        messages.append(
            f"{ticker} → {label} ({allocation}%)\n"
            f"Price: ${price} | vs 200DMA: {dist}%\n"
        )

    except Exception as e:
        messages.append(f"{ticker} → ERROR: {str(e)}")

# ================= FINAL MESSAGE =================
final_msg = "📊 Smart Allocation Signals\n\n" + "\n".join(messages)

send_msg(final_msg)

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
    res = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    print(res.json())

# ================= CONFIG =================
TICKERS = ["META", "AMZN", "AAPL", "MSFT", "GOOGL", "NVDA", "NFLX", "MELI", "QQQ"]
API_KEY = os.environ["TIINGO_API_KEY"]

END_DATE = datetime.today().date()
START_DATE = END_DATE - timedelta(days=3*365)

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

# ================= CLASSIFY =================
def classify_stock(df):
    df["50DMA"] = df["close"].rolling(50).mean()
    df["200DMA"] = df["close"].rolling(200).mean()

    df = df.dropna()

    trend_ratio = (df["close"] > df["200DMA"]).mean()
    dip_freq = (df["close"] < df["50DMA"]).mean()
    volatility = df["close"].pct_change().std()

    if trend_ratio > 0.7 and dip_freq < 0.2:
        return "TREND"
    elif volatility > 0.025:
        return "VOLATILE"
    else:
        return "HYBRID"

# ================= SIGNAL =================
def generate_signal(df, stock_type):
    latest = df.iloc[-1]

    price = latest["close"]
    dma50 = latest["50DMA"]
    dma200 = latest["200DMA"]
    rsi = latest["RSI"]

    if stock_type == "TREND":
        if price < dma200 and dma50 > dma200:
            return "🔥 STRONG BUY (Trend Dip)"
        elif price < dma50:
            return "🟢 ADD (Pullback)"
        else:
            return "HOLD"

    # HYBRID + VOLATILE
    if price < dma200 and rsi < 40:
        return "🔥 STRONG BUY (Deep Value)"
    elif price < dma50 and price > dma200 and 35 < rsi < 55:
        return "🟡 BUY (Pullback)"
    elif price > dma50 and dma50 > dma200 and 50 < rsi < 70:
        return "🟢 BUY (Momentum)"
    else:
        return "HOLD"

# ================= RUN =================
messages = []

for ticker in TICKERS:
    try:
        df = fetch_data(ticker)

        df["50DMA"] = df["close"].rolling(50).mean()
        df["200DMA"] = df["close"].rolling(200).mean()
        df["RSI"] = compute_rsi(df["close"])

        df = df.dropna()

        stock_type = classify_stock(df)
        signal = generate_signal(df, stock_type)
        price = round(df.iloc[-1]["close"], 2)

        messages.append(f"{ticker} ({stock_type}) → {signal} | ${price}")

    except Exception as e:
        messages.append(f"{ticker} → ERROR: {str(e)}")

# ================= FINAL MESSAGE =================
final_msg = "📊 Daily Stock Signals\n\n" + "\n".join(messages)

send_msg(final_msg)

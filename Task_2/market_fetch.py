import yfinance as yf
from pycoingecko import CoinGeckoAPI
from datetime import datetime
import logging

logging.basicConfig(level=logging.ERROR)


def fetch_crypto_price(symbol="bitcoin"):
    try:
        cg = CoinGeckoAPI()
        data = cg.get_price(ids=symbol, vs_currencies="usd")
        price = data[symbol]["usd"]
        return ("BTC", price, "USD")
    except Exception as e:
        logging.error(f"Crypto fetch failed: {e}")
        return None


def fetch_stock_price(symbol="^NSEI"):
    try:
        ticker = yf.Ticker(symbol)
        price = ticker.history(period="1d")["Close"].iloc[-1]
        return ("NIFTY50", price, "INR")
    except Exception as e:
        logging.error(f"Stock fetch failed: {e}")
        return None


def fetch_gold_price():
    try:
        ticker = yf.Ticker("GC=F")
        price = ticker.history(period="1d")["Close"].iloc[-1]
        return ("GOLD", price, "USD/oz")
    except Exception as e:
        logging.error(f"Gold fetch failed: {e}")
        return None


def format_price(price):
    return f"{price:,.2f}"


def print_table(data):
    print("\nAsset Prices - fetched at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("-" * 55)
    print(f"{'Asset':10} | {'Price':15} | {'Currency'}")
    print("-" * 55)

    for item in data:
        if item:
            name, price, currency = item
            price = format_price(price)
        else:
            name, price, currency = "ERROR", "-", "-"

        print(f"{name:10} | {price:<15} | {currency}")


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    results = []

    results.append(fetch_crypto_price())
    results.append(fetch_stock_price())
    results.append(fetch_gold_price())

    print_table(results)
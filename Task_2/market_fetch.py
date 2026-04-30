import logging
from datetime import datetime

import yfinance as yf
from pycoingecko import CoinGeckoAPI
from tabulate import tabulate

GRAMS_PER_TROY_OUNCE = 31.1034768

logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")

cg = CoinGeckoAPI()
TIMEZONE = "IST"


# ---------------- DATA FETCH ---------------- #

def fetch_crypto_price():
    try:
        data = cg.get_price(ids="bitcoin", vs_currencies="usd")
        return ("BTC", float(data["bitcoin"]["usd"]), "USD")
    except Exception as e:
        logging.error(f"Crypto fetch failed: {e}")
        return ("BTC", None, "USD")


def fetch_stock_price():
    try:
        price = yf.Ticker("^NSEI").history(period="1d")["Close"].iloc[-1]
        return ("NIFTY50", float(price), "INR")
    except Exception as e:
        logging.error(f"Stock fetch failed: {e}")
        return ("NIFTY50", None, "INR")


def fetch_gold_price():
    try:
        gold = yf.Ticker("GC=F").history(period="1d")["Close"].iloc[-1]
        fx = yf.Ticker("USDINR=X").history(period="1d")["Close"].iloc[-1]

        price = (gold * fx) / GRAMS_PER_TROY_OUNCE
        return ("GOLD", float(price), "INR/g")
    except Exception as e:
        logging.error(f"Gold fetch failed: {e}")
        return ("GOLD", None, "INR/g")


# ---------------- FORMAT + PRINT ---------------- #

def format_price(p):
    return "ERROR" if p is None else f"{p:,.2f}"


def print_table(rows):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\nAsset Prices — fetched at {ts} {TIMEZONE}\n")

    table = [[name, format_price(price), currency] for name, price, currency in rows]

    print(tabulate(
        table,
        headers=["Asset", "Price", "Currency"],
        tablefmt="grid",
        disable_numparse=True  # prevents tabulate from messing with formatting
    ))


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    results = [
        fetch_crypto_price(),
        fetch_stock_price(),
        fetch_gold_price()
    ]

    print_table(results)
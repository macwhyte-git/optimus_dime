import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

load_dotenv

api_key = os.getenv("ALPACA_API_KEY")
secret_key = os.getenv("ALPACA_SECRET_KEY")
paper = os.getenv("ALPACA_PAPER", "true").lower() == "true"

if not api_key or not secret_key:
    raise SystemExit("Missing ALPACA_API_KEY or ALPACA_SECRET_KEY in .env")

client = TradingClient(api_key, secret_key, paper=paper)
account = client.get_account()

print("Connected to Alpaca")
print("Mode:", "paper" if paper else "LIVE")
print("Account status:", account.status)
print("Buying power:", account.buying_power)
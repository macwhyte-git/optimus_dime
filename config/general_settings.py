import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

#Alpaca API credentials
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_API_SECRET = os.getenv("ALPACA_API_SECRET")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL")

# API Documentation:
# https://alpaca.markets/sdks/python/market_data.html

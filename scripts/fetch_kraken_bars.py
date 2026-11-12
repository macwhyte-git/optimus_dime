import requests
import pandas as pd

url = "https://api.kraken.com/0/public/OHLC"
resp = requests.get(url, params={"pair": "XBTUSD", "interval": 5}, timeout=10)
resp.raise_for_status()
payload = resp.json()

if payload["error"]:
    raise SystemExit(payload["error"])

result = payload["result"]
pair_key = next(k for k in result if k != "last")

cols = ["timestamp", "open", "high", "low", "close", "vwap", "volume", "trade_count"]
df = pd.DataFrame(result[pair_key], columns=cols)
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
df[["open", "high", "low", "close", "vwap", "volume"]] = df[
    ["open", "high", "low", "close", "vwap", "volume"]
].astype(float)
df["trade_count"] = df["trade_count"].astype(int)
df = df.set_index("timestamp")

print(df.tail())
print("Rows returned:", len(df))
print("Median volume:", df["volume"].median())
print("Median trade count:", df["trade_count"].median())
print("Bars with 0 volume:", (df["volume"] == 0).sum())
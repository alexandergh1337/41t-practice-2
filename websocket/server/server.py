import asyncio
import json
import random
import time
import websockets
from websockets.exceptions import ConnectionClosed

PORT = 8000
VALID_TOKEN = "demo_token"
TICKERS = ["AAPL", "GOOG", "MSFT", "TSLA"]

subscriptions = {}

async def price_generator():
    prices = {t: random.uniform(100, 500) for t in TICKERS}
    while True:
        for t in TICKERS:
            prices[t] += random.uniform(-1, 1)
            prices[t] = round(prices[t], 2)
        yield {t: (p, int(time.time())) for t, p in prices.items()}
        await asyncio.sleep(1)

async def send_price_updates():
    gen = price_generator()
    async for prices in gen:
        for ws, tickers in list(subscriptions.items()):
            for t in tickers:
                if t in prices:
                    msg = {
                        "event": "priceUpdate",
                        "ticker": t,
                        "price": prices[t][0],
                        "ts": prices[t][1]
                    }
                    try:
                        await ws.send(json.dumps(msg))
                    except ConnectionClosed:
                        subscriptions.pop(ws, None)

async def handler(ws):
    try:
        async for msg in ws:
            try:
                data = json.loads(msg)
            except Exception:
                await ws.send(json.dumps({"event": "error", "message": "Invalid JSON"}))
                continue
            if data.get("event") == "subscribe":
                token = data.get("token")
                tickers = data.get("tickers", [])
                if token != VALID_TOKEN:
                    await ws.send(json.dumps({"event": "error", "message": "Invalid token"}))
                    continue
                if not isinstance(tickers, list) or not all(isinstance(t, str) for t in tickers):
                    await ws.send(json.dumps({"event": "error", "message": "Invalid tickers"}))
                    continue

                tickers = [t for t in tickers if t in TICKERS]
                subscriptions[ws] = set(tickers)
                await ws.send(json.dumps({"event": "subscribed", "tickers": tickers}))
            elif data.get("event") == "unsubscribe":
                tickers = data.get("tickers", [])
                if ws in subscriptions:
                    subscriptions[ws] -= set(tickers)
                    await ws.send(json.dumps({"event": "unsubscribed", "tickers": tickers}))
            else:
                await ws.send(json.dumps({"event": "error", "message": "Unknown event"}))
    finally:
        subscriptions.pop(ws, None)

async def main():
    async with websockets.serve(handler, "0.0.0.0", PORT):
        await send_price_updates()

if __name__ == "__main__":
    asyncio.run(main())

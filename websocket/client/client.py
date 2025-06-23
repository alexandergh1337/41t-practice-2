import asyncio
import websockets
import json

WS_URL = "ws://localhost:8000"
TOKEN = "demo_token"
TICKERS = ["AAPL", "GOOG"]

async def main():
    async with websockets.connect(WS_URL) as ws:
        subscribe_msg = {
            "event": "subscribe",
            "tickers": TICKERS,
            "token": TOKEN
        }
        await ws.send(json.dumps(subscribe_msg))
        print(f"Подписка: {subscribe_msg}")

        async def unsubscribe():
            await asyncio.sleep(5)
            unsub_msg = {
                "event": "unsubscribe",
                "tickers": [TICKERS[0]]
            }
            await ws.send(json.dumps(unsub_msg))
            print(f"Отписка: {unsub_msg}")

        unsub_task = asyncio.create_task(unsubscribe())

        try:
            async for msg in ws:
                try:
                    data = json.loads(msg)
                except Exception:
                    print(f"Некорректный JSON: {msg}")
                    continue
                if data.get("event") == "priceUpdate":
                    print(f"{data['ticker']}: {data['price']} (метка времени={data['ts']})")
                elif data.get("event") == "subscribed":
                    print(f"Подписка подтверждена: {data['tickers']}")
                elif data.get("event") == "unsubscribed":
                    print(f"Отписка подтверждена: {data['tickers']}")
                elif data.get("event") == "error":
                    print(f"Ошибка: {data['message']}")
                else:
                    print(f"{data}")
        except websockets.ConnectionClosed:
            print("Соединение закрыто")

if __name__ == "__main__":
    asyncio.run(main())

import requests
import json
import asyncio
import websockets

API_URL = "http://localhost:8000/graphql"

def add_product(name, quantity):
    query = '''
    mutation($name: String!, $quantity: Int!) {
      addProduct(name: $name, quantity: $quantity) {
        id
        name
        quantity
      }
    }
    '''
    variables = {"name": name, "quantity": quantity}
    resp = requests.post(API_URL, json={"query": query, "variables": variables})
    print("Добавлен товар:", resp.json())

def list_products():
    query = '''
    query {
      listProducts {
        id
        name
        quantity
      }
    }
    '''
    resp = requests.post(API_URL, json={"query": query})
    print("Список товаров:", json.dumps(resp.json(), ensure_ascii=False, indent=2))

def update_stock(product_id, delta):
    query = '''
    mutation($productId: ID!, $delta: Int!) {
      updateStock(productId: $productId, delta: $delta) {
        id
        name
        quantity
      }
    }
    '''
    variables = {"productId": product_id, "delta": delta}
    resp = requests.post(API_URL, json={"query": query, "variables": variables})
    print("Обновлен товар:", resp.json())

def remove_product(product_id):
    query = '''
    mutation($id: ID!) {
      removeProduct(id: $id)
    }
    '''
    variables = {"id": product_id}
    resp = requests.post(API_URL, json={"query": query, "variables": variables})
    print("Удаление товара:", resp.json())

def get_product(product_id):
    query = '''
    query($id: ID!) {
      getProduct(id: $id) {
        id
        name
        quantity
      }
    }
    '''
    variables = {"id": product_id}
    resp = requests.post(API_URL, json={"query": query, "variables": variables})
    print("Товар по id:", json.dumps(resp.json(), ensure_ascii=False, indent=2))

async def subscribe_stock_alerts(threshold=5):
    uri = "ws://localhost:8000/graphql"
    async with websockets.connect(uri, subprotocols=["graphql-transport-ws"]) as ws:
        await ws.send(json.dumps({"type": "connection_init", "payload": {}}))
        await ws.recv()

        await ws.send(json.dumps({
            "id": "1",
            "type": "subscribe",
            "payload": {
                "query": """
                    subscription($threshold: Int!) {
                        streamStockAlerts(threshold: $threshold) {
                            product { id name quantity }
                            message
                        }
                    }
                """,
                "variables": {"threshold": threshold}
            }
        }))
        print("Ожидание оповещений о низком остатке...")

        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get("type") == "next":
                print("[ОПОВЕЩЕНИЕ]", json.dumps(data["payload"], ensure_ascii=False, indent=2))
                break
            elif data.get("type") in ("complete", "error"):
                print("[КОНЕЦ]", data)
                break

if __name__ == "__main__":
    add_product("Тестовый товар", 10)
    r = requests.post(API_URL, json={"query": "{ listProducts { id } }"})
    first_id = r.json()["data"]["listProducts"][0]["id"]
    get_product(first_id)
    update_stock(first_id, -7)
    list_products()
    print("\nПример подписки на оповещения")
    asyncio.run(subscribe_stock_alerts(threshold=5))
    remove_product(first_id)

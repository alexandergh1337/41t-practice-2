import strawberry
from strawberry.fastapi import GraphQLRouter
from fastapi import FastAPI, HTTPException
from typing import List, Optional, AsyncGenerator
import json
import os
import uuid
import asyncio

PRODUCTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'products.json')

@strawberry.type
class Product:
    id: strawberry.ID
    name: str
    quantity: int

@strawberry.type
class StockChange:
    id: strawberry.ID
    product_id: strawberry.ID
    delta: int
    timestamp: str

@strawberry.type
class StockAlert:
    product: Product
    message: str

def load_products():
    if not os.path.exists(PRODUCTS_FILE):
        return []
    with open(PRODUCTS_FILE, 'r') as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, 'w') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

class PubSub:
    def __init__(self):
        self.subscribers = []
    async def publish(self, alert):
        for queue in self.subscribers:
            await queue.put(alert)
    async def subscribe(self):
        queue = asyncio.Queue()
        self.subscribers.append(queue)
        try:
            while True:
                alert = await queue.get()
                yield alert
        finally:
            self.subscribers.remove(queue)

pubsub = PubSub()

@strawberry.type
class Query:
    @strawberry.field
    def get_product(self, id: strawberry.ID) -> Optional[Product]:
        products = load_products()
        for p in products:
            if p['id'] == id:
                return Product(**p)
        return None

    @strawberry.field
    def list_products(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Product]:
        products = load_products()
        items = products[offset or 0:]
        if limit:
            items = items[:limit]
        return [Product(**p) for p in items]

@strawberry.type
class Mutation:
    @strawberry.field
    def add_product(self, name: str, quantity: int) -> Product:
        if quantity < 0:
            raise HTTPException(status_code=400, detail="Количество не может быть отрицательным")
        products = load_products()
        new_product = {
            'id': str(uuid.uuid4()),
            'name': name,
            'quantity': quantity
        }
        products.append(new_product)
        save_products(products)
        return Product(**new_product)

    @strawberry.field
    def update_stock(self, product_id: strawberry.ID, delta: int) -> Product:
        products = load_products()
        for p in products:
            if p['id'] == product_id:
                new_quantity = p['quantity'] + delta
                if new_quantity < 0:
                    raise HTTPException(status_code=400, detail="Итоговое количество не может быть отрицательным")
                p['quantity'] = new_quantity
                save_products(products)
                if p['quantity'] <= 5:
                    alert = StockAlert(product=Product(**p), message=f"Низкий запас: {p['name']} (кол-во={p['quantity']})")
                    asyncio.create_task(pubsub.publish(alert))
                return Product(**p)
        raise HTTPException(status_code=404, detail="Товар не найден")

    @strawberry.field
    def remove_product(self, id: strawberry.ID) -> bool:
        products = load_products()
        for i, p in enumerate(products):
            if p['id'] == id:
                del products[i]
                save_products(products)
                return True
        return False

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def stream_stock_alerts(self, threshold: int = 5) -> AsyncGenerator[StockAlert, None]:
        async for alert in pubsub.subscribe():
            if alert.product.quantity <= threshold:
                yield alert

schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)

app = FastAPI()
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

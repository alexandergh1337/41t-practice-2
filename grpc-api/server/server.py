import grpc
from concurrent import futures
import time
import threading
import json
import os

import inventory_pb2
import inventory_pb2_grpc

PRODUCTS_FILE = 'products.json'

class InventoryService(inventory_pb2_grpc.InventoryServiceServicer):
    def __init__(self):
        self.products = {}
        self.stock_alert_subscribers = []
        self.lock = threading.Lock()
        self._load_products()

    def _load_products(self):
        if os.path.exists(PRODUCTS_FILE):
            with open(PRODUCTS_FILE, 'r') as f:
                data = json.load(f)
                for prod in data:
                    self.products[prod['id']] = prod

    def _save_products(self):
        with open(PRODUCTS_FILE, 'w') as f:
            json.dump(list(self.products.values()), f)

    def AddProduct(self, request, context):
        with self.lock:
            prod_id = str(int(time.time() * 1000))
            product = {
                'id': prod_id,
                'name': request.name,
                'quantity': request.quantity
            }
            self.products[prod_id] = product
            self._save_products()
            return inventory_pb2.AddProductResponse(product=inventory_pb2.Product(**product))

    def GetProduct(self, request, context):
        prod = self.products.get(request.id)
        if not prod:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Товар не найден')
            return inventory_pb2.GetProductResponse()
        return inventory_pb2.GetProductResponse(product=inventory_pb2.Product(**prod))

    def UpdateStock(self, request, context):
        with self.lock:
            prod = self.products.get(request.id)
            if not prod:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details('Товар не найден')
                return inventory_pb2.UpdateStockResponse()
            prod['quantity'] += request.delta
            change = inventory_pb2.StockChange(product_id=prod['id'], delta=request.delta, timestamp=int(time.time()))
            self._save_products()

            if prod['quantity'] <= 5:
                self._notify_stock_alerts(prod)
            return inventory_pb2.UpdateStockResponse(product=inventory_pb2.Product(**prod), change=change)

    def RemoveProduct(self, request, context):
        with self.lock:
            if request.id in self.products:
                del self.products[request.id]
                self._save_products()
                return inventory_pb2.RemoveProductResponse(success=True)
            else:
                return inventory_pb2.RemoveProductResponse(success=False)

    def ListProducts(self, request, context):
        return inventory_pb2.ListProductsResponse(products=[inventory_pb2.Product(**prod) for prod in self.products.values()])

    def StreamStockAlerts(self, request, context):
        threshold = request.threshold if request.threshold > 0 else 5
        event = threading.Event()
        subscriber = {'event': event, 'context': context, 'threshold': threshold}
        self.stock_alert_subscribers.append(subscriber)
        try:
            for prod in self.products.values():
                if prod['quantity'] <= threshold:
                    alert = inventory_pb2.StockAlert(
                        product=inventory_pb2.Product(**prod),
                        message=f"Низкий запас: {prod['name']} (кол-во={prod['quantity']})"
                    )
                    yield alert

            while True:
                event.wait()
                for prod in self.products.values():
                    if prod['quantity'] <= threshold:
                        alert = inventory_pb2.StockAlert(
                            product=inventory_pb2.Product(**prod),
                            message=f"Низкий запас: {prod['name']} (кол-во={prod['quantity']})"
                        )
                        yield alert
                event.clear()
        finally:
            self.stock_alert_subscribers.remove(subscriber)

    def _notify_stock_alerts(self, prod):
        for sub in self.stock_alert_subscribers:
            if prod['quantity'] <= sub['threshold']:
                sub['event'].set()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inventory_pb2_grpc.add_InventoryServiceServicer_to_server(InventoryService(), server)
    server.add_insecure_port('[::]:50051')
    print('gRPC сервер запущен на порту 50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()

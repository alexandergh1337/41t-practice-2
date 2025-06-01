import grpc
import time
import threading
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../server')))
import inventory_pb2
import inventory_pb2_grpc

def print_product(product):
    print(f"Товар: id={product.id}, название={product.name}, кол-во={product.quantity}")

def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = inventory_pb2_grpc.InventoryServiceStub(channel)

    print("\nДобавить товар")
    resp = stub.AddProduct(inventory_pb2.AddProductRequest(name="Тестовый товар", quantity=10))
    print_product(resp.product)
    prod_id = resp.product.id

    print("\nПолучить товар")
    resp = stub.GetProduct(inventory_pb2.GetProductRequest(id=prod_id))
    print_product(resp.product)

    print("\nОбновить запас")
    resp = stub.UpdateStock(inventory_pb2.UpdateStockRequest(id=prod_id, delta=-7))
    print_product(resp.product)
    print(f"Изменение запаса: разница={resp.change.delta}, метка времени={resp.change.timestamp}")

    print("\nСписок товаров")
    resp = stub.ListProducts(inventory_pb2.ListProductsRequest())
    for p in resp.products:
        print_product(p)

    print("\nОповещения о низком запасе")
    def stock_alerts():
        for alert in stub.StreamStockAlerts(inventory_pb2.StreamStockAlertsRequest(threshold=5)):
            print(f"[ОПОВЕЩЕНИЕ] {alert.message}")
    t = threading.Thread(target=stock_alerts, daemon=True)
    t.start()
    time.sleep(1)

    print("\nОбновить запас")
    stub.UpdateStock(inventory_pb2.UpdateStockRequest(id=prod_id, delta=-3))
    time.sleep(2)

    print("\nУдалить товар")
    resp = stub.RemoveProduct(inventory_pb2.RemoveProductRequest(id=prod_id))
    print(f"Удаление успешно: {resp.success}")
    time.sleep(1)

if __name__ == '__main__':
    run()

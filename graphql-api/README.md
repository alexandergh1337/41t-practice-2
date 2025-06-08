# Inventory Management GraphQL API

## Описание

GraphQL-сервис для управления складскими остатками. Позволяет добавлять, получать, изменять и удалять товары, а также получать оповещения о низком остатке через подписку.

**Стек:**
- Язык: Python 3.10+
- GraphQL: Strawberry + FastAPI
- Хранилище: JSON-файл
- Подписки: WebSocket (через Strawberry)

## Установка и запуск

1. **Клонируйте репозиторий и перейдите в папку:**
   ```bash
   cd graphql-api
   ```

2. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Запустите сервер:**
   ```bash
   cd server
   uvicorn server:app --reload
   ```
   Сервер будет доступен по адресу http://localhost:8000/graphql

4. **В другой консоли запустите клиентские примеры:**
   ```bash
   cd client
   python client.py
   ```

## Примеры GraphQL-запросов

### Добавить товар
```graphql
mutation {
  addProduct(name: "Тестовый товар", quantity: 10) {
    id
    name
    quantity
  }
}
```

### Получить список товаров
```graphql
query {
  listProducts {
    id
    name
    quantity
  }
}
```

### Обновить запас
```graphql
mutation {
  updateStock(productId: "<ID>", delta: -5) {
    id
    name
    quantity
  }
}
```

### Удалить товар
```graphql
mutation {
  removeProduct(id: "<ID>")
}
```

### Подписка на оповещения о низком остатке
```graphql
subscription {
  streamStockAlerts(threshold: 5) {
    product { id name quantity }
    message
  }
}
```

### Получить товар по id
```graphql
query {
  getProduct(id: "<ID>") {
    id
    name
    quantity
  }
}
```

## Структура проекта
```
~/graphql-api/
├── client/
│   └── client.py
├── schema/
│   └── inventory.graphql
├── server/
│   └── server.py
├── products.json
├── README.md
└── requirements.txt
```

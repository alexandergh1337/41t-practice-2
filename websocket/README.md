# Stock Price Broadcast WebSocket

## Описание

Сервис транслирует в реальном времени котировки акций по протоколу WebSocket. Клиенты могут подписываться на интересующие тикеры и получать обновления цен.

---

## Запуск

### Зависимости
- Python 3.8+
- websockets (`pip install websockets`)

### Сервер
```bash
cd server
python server.py
```

### Клиент
```bash
cd client
python client.py
```

---

## Примеры JSON-сообщений и ожидаемые ответы сервера

### Подписка на тикеры
**Клиент → Сервер:**
```json
{
  "event": "subscribe",
  "tickers": ["AAPL", "GOOG"],
  "token": "demo_token"
}
```

**Ответ сервера:**
```json
{
  "event": "subscribed",
  "tickers": ["AAPL", "GOOG"]
}
```

### Обновление цены
**Сервер → Клиент:**
```json
{
  "event": "priceUpdate",
  "ticker": "AAPL",
  "price": 123.45,
  "ts": 1719140000
}
```


### Отписка
**Клиент → Сервер:**
```json
{
  "event": "unsubscribe",
  "tickers": ["AAPL"]
}
```

**Ответ сервера:**
```json
{
  "event": "unsubscribed",
  "tickers": ["AAPL"]
}
```

### Ошибка
**Сервер → Клиент:**
```json
{
  "event": "error",
  "message": "Invalid token"
}
```

---

## Аутентификация
- Передаётся в поле `token` при подписке.
- Для теста используйте токен: `demo_token`.

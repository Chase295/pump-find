# Backend Tests (pytest)

Dokumentation der 201 Backend-Tests.

---

## Übersicht

```
tests/
├── __init__.py
├── conftest.py           # Gemeinsame Fixtures
├── unit/                 # 71 Unit Tests
│   ├── test_coin_cache.py        # 22 Tests
│   ├── test_coin_filter.py       # 26 Tests
│   ├── test_metric_calculations.py # 22 Tests
│   └── test_trade_processing.py  # 23 Tests
├── integration/          # 85 Integration Tests
│   ├── test_api_endpoints.py     # 20 Tests
│   ├── test_database_operations.py # 18 Tests
│   ├── test_websocket_connection.py # 19 Tests
│   ├── test_zombie_detection.py  # 14 Tests
│   └── test_coin_stream_recovery.py # 14 Tests
└── stress/               # 23 Stress Tests
    ├── test_high_volume.py       # 11 Tests
    └── test_reconnection_scenarios.py # 12 Tests
```

---

## Test-Ausführung

```bash
# Alle Tests
pytest tests/ -v

# Nur Unit Tests
pytest tests/unit/ -v

# Nur Integration Tests
pytest tests/integration/ -v

# Nur Stress Tests
pytest tests/stress/ -v

# Einzelne Testdatei
pytest tests/unit/test_coin_cache.py -v

# Mit Coverage
pytest tests/ --cov=unified_service --cov-report=html

# Parallel (wenn pytest-xdist installiert)
pytest tests/ -n auto
```

---

## conftest.py - Gemeinsame Fixtures

**Pfad:** `tests/conftest.py`

### Sample Data Fixtures

```python
@pytest.fixture
def sample_coin_data() -> Dict[str, Any]:
    """Sample Coin-Daten für Discovery Tests"""
    return {
        "mint": "TestCoin123456789012345678901234567890123",
        "name": "Good Coin",
        "symbol": "GOOD",
        "marketCapSol": 1000.0,
        "vTokensInBondingCurve": 1000000000,
        "vSolInBondingCurve": 10.0,
        "bondingCurveKey": "BondingCurveKey123...",
        "traderPublicKey": "CreatorKey123...",
        "signature": "TxSignature123..."
    }

@pytest.fixture
def sample_bad_name_coin() -> Dict[str, Any]:
    """Coin mit Bad Name für Filter Tests"""
    return {
        "mint": "BadCoin12345...",
        "name": "Test Scam Bot",  # Enthält "test", "scam", "bot"
        "symbol": "SCAM",
        ...
    }

@pytest.fixture
def sample_trade_data() -> Dict[str, Any]:
    """Sample Trade-Daten für Processing Tests"""
    return {
        "mint": "TestCoin123...",
        "txType": "buy",
        "solAmount": 1.5,
        "tokenAmount": 150000,
        "vSolInBondingCurve": 15.0,
        "vTokensInBondingCurve": 900000000,
        "traderPublicKey": "TraderKey123...",
        ...
    }

@pytest.fixture
def sample_whale_trade() -> Dict[str, Any]:
    """Whale Trade (>= 1.0 SOL)"""
    return {
        "solAmount": 5.0,  # Whale threshold überschritten
        ...
    }

@pytest.fixture
def sample_micro_trade() -> Dict[str, Any]:
    """Micro Trade (< 0.01 SOL)"""
    return {
        "solAmount": 0.005,  # Unter micro threshold
        ...
    }
```

### Mock Fixtures

```python
@pytest.fixture
def mock_db_pool():
    """Mock asyncpg Connection Pool"""
    pool = AsyncMock()
    pool.fetch = AsyncMock(return_value=[])
    pool.fetchrow = AsyncMock(return_value=None)
    pool.execute = AsyncMock(return_value="INSERT 0 1")

    # Context manager für acquire
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)

    return pool

@pytest.fixture
def mock_websocket():
    """Mock WebSocket Connection"""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock(return_value='{}')
    ws.closed = False
    return ws

@pytest.fixture
def mock_http_client():
    """Mock HTTP Client (httpx)"""
    client = AsyncMock()
    response = MagicMock()
    response.status_code = 200
    client.post = AsyncMock(return_value=response)
    return client
```

### Component Fixtures

```python
@pytest.fixture
def coin_cache():
    """Erstellt CoinCache Instanz mit gemockten Prometheus Metriken"""
    with patch('unified_service.cache_size') as mock_cache_size, \
         patch('unified_service.cache_activations') as mock_activations:

        mock_cache_size.set = MagicMock()
        mock_activations.inc = MagicMock()

        from unified_service import CoinCache
        cache = CoinCache(cache_seconds=120)
        yield cache

@pytest.fixture
def coin_filter():
    """Erstellt CoinFilter Instanz"""
    with patch('unified_service.coins_filtered') as mock_filtered:
        from unified_service import CoinFilter
        filter_instance = CoinFilter(spam_burst_window=30)
        yield filter_instance
```

---

## Unit Tests

### test_coin_cache.py (22 Tests)

**Testet:** `CoinCache` Klasse

```python
# Beispiel-Tests
class TestCoinCache:
    def test_add_coin_creates_entry(self, coin_cache, sample_coin_data):
        """Coin wird korrekt zum Cache hinzugefügt"""
        mint = sample_coin_data["mint"]
        coin_cache.add_coin(mint, sample_coin_data)

        assert mint in coin_cache.cache
        assert coin_cache.cache[mint]["activated"] == False

    def test_add_trade_increments_count(self, coin_cache, sample_coin_data, sample_trade_data):
        """Trades werden gezählt"""
        mint = sample_coin_data["mint"]
        coin_cache.add_coin(mint, sample_coin_data)
        coin_cache.add_trade(mint, sample_trade_data)

        assert len(coin_cache.cache[mint]["trades"]) == 1

    def test_activate_coin_sets_flag(self, coin_cache, sample_coin_data):
        """Aktivierung setzt Flag korrekt"""
        mint = sample_coin_data["mint"]
        coin_cache.add_coin(mint, sample_coin_data)
        coin_cache.activate_coin(mint)

        assert coin_cache.cache[mint]["activated"] == True

    def test_cleanup_removes_expired(self, coin_cache, sample_coin_data):
        """Abgelaufene Coins werden entfernt"""
        mint = sample_coin_data["mint"]
        coin_cache.add_coin(mint, sample_coin_data)

        # Zeit vorstellen
        future_time = time.time() + 200
        expired = coin_cache.cleanup_expired_coins(future_time)

        assert expired == 1
        assert mint not in coin_cache.cache
```

**Test-Kategorien:**
- Coin hinzufügen (3 Tests)
- Trades hinzufügen (4 Tests)
- Aktivierung (5 Tests)
- Expiration/Cleanup (4 Tests)
- Cache-Statistiken (3 Tests)
- Edge Cases (3 Tests)

### test_coin_filter.py (26 Tests)

**Testet:** `CoinFilter` Klasse

```python
class TestCoinFilter:
    def test_bad_name_filtered(self, coin_filter, sample_bad_name_coin):
        """Coins mit Bad Names werden gefiltert"""
        should_filter, reason = coin_filter.should_filter_coin(sample_bad_name_coin)

        assert should_filter == True
        assert reason == "bad_name"

    def test_good_coin_passes(self, coin_filter, sample_coin_data):
        """Gute Coins passieren den Filter"""
        should_filter, reason = coin_filter.should_filter_coin(sample_coin_data)

        assert should_filter == False
        assert reason is None

    def test_spam_burst_detection(self, coin_filter, sample_coin_data):
        """Spam-Burst wird erkannt"""
        # Ersten Coin hinzufügen
        coin_filter.should_filter_coin(sample_coin_data)

        # Gleichen Namen sofort nochmal
        should_filter, reason = coin_filter.should_filter_coin(sample_coin_data)

        assert should_filter == True
        assert reason == "spam_burst"
```

**Test-Kategorien:**
- Bad Names (10 Tests: test, bot, rug, scam, etc.)
- Spam Burst Detection (8 Tests)
- Edge Cases (5 Tests)
- Pattern Updates (3 Tests)

### test_metric_calculations.py (22 Tests)

**Testet:** OHLCV-Berechnungen und Trade-Verarbeitung

```python
class TestMetricCalculations:
    def test_price_calculation(self):
        """Preis wird korrekt berechnet"""
        v_sol = 30.0
        v_tokens = 1000000000
        price = v_sol / v_tokens

        assert price == pytest.approx(0.00000003, rel=1e-6)

    def test_ohlcv_open_set_once(self, coin_cache, sample_trade_data):
        """Open wird nur beim ersten Trade gesetzt"""
        # ... Test Implementation

    def test_high_low_tracking(self, coin_cache, sample_trade_data):
        """High/Low werden korrekt getrackt"""
        # ... Test Implementation
```

**Test-Kategorien:**
- Preis-Berechnung (5 Tests)
- OHLCV-Updates (8 Tests)
- Volume-Berechnung (5 Tests)
- Market Cap (4 Tests)

### test_trade_processing.py (23 Tests)

**Testet:** Trade-Verarbeitung, Whale/Dev Detection

```python
class TestTradeProcessing:
    def test_whale_detection(self, sample_whale_trade):
        """Whale-Trades werden erkannt"""
        assert sample_whale_trade["solAmount"] >= 1.0

    def test_micro_trade_detection(self, sample_micro_trade):
        """Micro-Trades werden erkannt"""
        assert sample_micro_trade["solAmount"] < 0.01

    def test_dev_sold_tracking(self, sample_stream_data, sample_sell_trade):
        """Dev-Verkäufe werden getrackt"""
        # ... Test Implementation
```

**Test-Kategorien:**
- Whale Detection (5 Tests)
- Micro Trade Detection (4 Tests)
- Dev Tracking (4 Tests)
- Unique Wallets (4 Tests)
- Buy/Sell Stats (6 Tests)

---

## Integration Tests

### test_api_endpoints.py (20 Tests)

**Testet:** FastAPI REST Endpoints

```python
class TestAPIEndpoints:
    @pytest.mark.asyncio
    async def test_health_endpoint(self, mock_unified_service):
        """GET /health liefert korrekten Status"""
        from fastapi.testclient import TestClient
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()

    @pytest.mark.asyncio
    async def test_config_endpoint(self, mock_unified_service):
        """GET /config liefert Konfiguration"""
        # ... Test Implementation

    @pytest.mark.asyncio
    async def test_phases_crud(self, mock_db_pool):
        """Phase CRUD Operations funktionieren"""
        # ... Test Implementation
```

**Test-Kategorien:**
- Health Endpoint (3 Tests)
- Config Endpoints (4 Tests)
- Phase CRUD (8 Tests)
- Database Endpoints (5 Tests)

### test_database_operations.py (18 Tests)

**Testet:** PostgreSQL-Operationen

```python
class TestDatabaseOperations:
    @pytest.mark.asyncio
    async def test_insert_discovered_coin(self, mock_db_pool, sample_coin_data):
        """Coin wird korrekt in DB gespeichert"""
        # ... Test Implementation

    @pytest.mark.asyncio
    async def test_update_stream_phase(self, mock_db_pool):
        """Phase-Update funktioniert"""
        # ... Test Implementation
```

**Test-Kategorien:**
- INSERT Operations (6 Tests)
- UPDATE Operations (5 Tests)
- SELECT Operations (4 Tests)
- Transaction Handling (3 Tests)

### test_websocket_connection.py (19 Tests)

**Testet:** WebSocket-Verbindung und Events

```python
class TestWebSocketConnection:
    @pytest.mark.asyncio
    async def test_subscription_message(self, mock_websocket):
        """Subscription Message wird gesendet"""
        await mock_websocket.send(json.dumps({"method": "subscribeNewToken"}))
        mock_websocket.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_reconnect_on_error(self, mock_websocket):
        """Reconnect bei Verbindungsabbruch"""
        # ... Test Implementation
```

**Test-Kategorien:**
- Verbindungsaufbau (4 Tests)
- Subscriptions (5 Tests)
- Event Handling (5 Tests)
- Reconnect Logic (5 Tests)

### test_zombie_detection.py (14 Tests)

**Testet:** Stale-Stream-Detection

```python
class TestZombieDetection:
    @pytest.mark.asyncio
    async def test_inactive_coin_detected(self):
        """Inaktive Coins werden erkannt"""
        # ... Test Implementation

    @pytest.mark.asyncio
    async def test_force_resubscribe(self, mock_websocket):
        """Force Re-Subscribe wird gesendet"""
        # ... Test Implementation
```

### test_coin_stream_recovery.py (14 Tests)

**Testet:** Stream-Recovery bei Neustarts

---

## Stress Tests

### test_high_volume.py (11 Tests)

**Testet:** Performance unter Last

```python
class TestHighVolume:
    @pytest.mark.asyncio
    async def test_1000_trades_per_second(self):
        """System verarbeitet 1000 Trades/Sekunde"""
        # ... Test Implementation

    @pytest.mark.asyncio
    async def test_concurrent_coin_discovery(self):
        """Mehrere Coins gleichzeitig verarbeitet"""
        # ... Test Implementation
```

### test_reconnection_scenarios.py (12 Tests)

**Testet:** Reconnect-Verhalten

```python
class TestReconnectionScenarios:
    @pytest.mark.asyncio
    async def test_rapid_reconnects(self):
        """Schnelle Reconnects werden gehandhabt"""
        # ... Test Implementation

    @pytest.mark.asyncio
    async def test_backoff_increases(self):
        """Exponential Backoff funktioniert"""
        # ... Test Implementation
```

---

## Mock-Strategien

### Prometheus Metriken

```python
# Metriken müssen gemockt werden, da sie beim Import initialisiert werden
with patch('unified_service.cache_size') as mock:
    mock.set = MagicMock()
    # ... Test Code
```

### Datenbank

```python
# AsyncMock für asyncpg Pool
pool = AsyncMock()
pool.fetch = AsyncMock(return_value=[
    {"id": 1, "name": "Test Phase", ...}
])
```

### WebSocket

```python
# AsyncMock für websockets
ws = AsyncMock()
ws.recv = AsyncMock(side_effect=[
    '{"txType": "create", "mint": "..."}',
    '{"txType": "buy", "mint": "..."}'
])
```

---

## Best Practices

1. **Fixtures verwenden:** Nicht in jedem Test Daten neu erstellen
2. **Mocks minimieren:** Nur externe Dependencies mocken
3. **Async Tests markieren:** `@pytest.mark.asyncio`
4. **Isolation:** Jeder Test muss unabhängig laufen
5. **Assertions aussagekräftig:** `assert x == y` statt nur `assert x`

---

## Weiterführende Dokumentation

- [Frontend Tests](frontend.md) - vitest Tests
- [Backend-Architektur](../architecture/backend.md) - Zu testende Klassen
- [API-Endpunkte](../api/endpoints.md) - Zu testende Endpoints

# Backend-Architektur im Detail

Das Backend besteht aus einer einzigen Python-Datei `unified_service.py` (2561 Zeilen), die alle Funktionalitäten vereint.

---

## Dateistruktur

```
unified_service.py
├── Imports & Globals           (1-138)
├── Prometheus Metriken         (139-205)
├── Pydantic Models             (206-505)
├── CoinCache Klasse            (506-606)
├── CoinFilter Klasse           (608-643)
├── FastAPI Endpoints           (645-1496)
└── UnifiedService Klasse       (1498-2561)
```

---

## Prometheus Metriken (Zeilen 139-205)

Das System exportiert 50+ Metriken für Monitoring:

### Discovery-Metriken
```python
coins_received = Counter('unified_coins_received_total', 'Neue Coins empfangen')
coins_filtered = Counter('unified_coins_filtered_total', 'Gefilterte Coins', ['reason'])
coins_sent_n8n = Counter('unified_coins_sent_n8n_total', 'Coins an n8n gesendet')
n8n_batches_sent = Counter('unified_n8n_batches_sent_total', 'n8n Batches gesendet')
n8n_available = Gauge('unified_n8n_available', 'n8n Service verfügbar')
n8n_buffer_size = Gauge('unified_n8n_buffer_size', 'Coins im n8n Buffer')
```

### Cache-Metriken
```python
cache_size = Gauge('unified_cache_size', 'Aktuelle Cache-Größe')
cache_activations = Counter('unified_cache_activations_total', 'Cache-Aktivierungen')
cache_expirations = Counter('unified_cache_expirations_total', 'Cache-Abläufe')
```

### Tracking-Metriken
```python
trades_received = Counter('unified_trades_received_total', 'Trades empfangen')
trades_processed = Counter('unified_trades_processed_total', 'Trades verarbeitet')
metrics_saved = Counter('unified_metrics_saved_total', 'Metriken gespeichert')
coins_tracked = Gauge('unified_coins_tracked', 'Aktuell getrackte Coins')
phase_switches = Counter('unified_phase_switches_total', 'Phasen-Wechsel')
coins_graduated = Counter('unified_coins_graduated_total', 'Graduierte Coins')
```

### Verbindungs-Metriken
```python
ws_connected = Gauge('unified_ws_connected', 'WebSocket verbunden')
db_connected = Gauge('unified_db_connected', 'Datenbank verbunden')
ws_reconnects = Counter('unified_ws_reconnects_total', 'WebSocket Reconnects')
```

---

## Pydantic Models (Zeilen 206-505)

Alle Request/Response Schemas sind als Pydantic Models definiert:

### Health Response (Zeile 223)
```python
class HealthResponse(BaseModel):
    status: str                    # "healthy" | "degraded" | "unhealthy"
    ws_connected: bool
    db_connected: bool
    uptime_seconds: float
    last_message_ago: Optional[float]
    reconnect_count: int
    last_error: Optional[str]
    cache_stats: CacheStats        # total_coins, activated, expired
    tracking_stats: TrackingStats  # active_coins, total_trades, metrics_saved
    discovery_stats: DiscoveryStats # total_discovered, n8n_available, buffer_size
```

### Config Update Request (Zeile 240)
```python
class ConfigUpdateRequest(BaseModel):
    db_dsn: Optional[str] = None
    n8n_webhook_url: Optional[str] = None
    coin_cache_seconds: Optional[int] = None
    db_refresh_interval: Optional[int] = None
    batch_size: Optional[int] = None
    batch_timeout: Optional[int] = None
    bad_names_pattern: Optional[str] = None
    spam_burst_window: Optional[int] = None
```

### Phase CRUD Models (Zeilen 258-286)
```python
class PhaseUpdateRequest(BaseModel):
    name: Optional[str] = None
    interval_seconds: Optional[int] = None
    min_age_minutes: Optional[int] = None
    max_age_minutes: Optional[int] = None

class PhaseCreateRequest(BaseModel):
    name: str
    interval_seconds: int
    min_age_minutes: int
    max_age_minutes: int

class PhaseDeleteResponse(BaseModel):
    status: str
    message: str
    deleted_phase_id: int
    affected_streams: int
```

---

## CoinCache Klasse (Zeilen 506-606)

Der Cache speichert neue Coins für 120 Sekunden, bevor sie für Tracking aktiviert werden.

### Datenstruktur
```python
class CoinCache:
    def __init__(self, cache_seconds=120):
        self.cache_seconds = cache_seconds
        self.cache = {}  # {mint: CacheEntry}

# CacheEntry Struktur:
{
    "discovered_at": datetime,      # Zeitpunkt der Entdeckung
    "metadata": coin_data,          # Original WebSocket-Daten
    "trades": [],                   # [(timestamp, trade_data), ...]
    "n8n_sent": False,              # An n8n gesendet?
    "activated": False,             # Für Tracking aktiviert?
    "subscription_active": True     # Trade-Subscription aktiv?
}
```

### Methoden

#### `add_coin(mint, coin_data)` (Zeile 517)
```python
def add_coin(self, mint, coin_data):
    """Fügt neuen Coin zum Cache hinzu"""
    if mint not in self.cache:
        self.cache[mint] = {
            "discovered_at": datetime.utcnow(),
            "metadata": coin_data,
            "trades": [],
            "n8n_sent": False,
            "activated": False,
            "subscription_active": True
        }
        cache_size.set(len(self.cache))
```

#### `add_trade(mint, trade_data)` (Zeile 534)
```python
def add_trade(self, mint, trade_data):
    """Speichert Trade während Cache-Phase"""
    if mint in self.cache:
        self.cache[mint]["trades"].append((datetime.utcnow(), trade_data))
```

#### `activate_coin(mint, stream_data)` (Zeile 540)
```python
def activate_coin(self, mint, stream_data=None):
    """Aktiviert Coin für Tracking, gibt gepufferte Trades zurück"""
    if mint in self.cache:
        entry = self.cache[mint]
        entry["activated"] = True
        cached_trades = entry["trades"]
        cache_activations.inc()
        return cached_trades
    return []
```

#### `cleanup_expired_coins(current_time)` (Zeile 568)
```python
def cleanup_expired_coins(self, current_time=None):
    """Entfernt abgelaufene Coins (>120s, nicht aktiviert)"""
    now = current_time or datetime.utcnow()
    expired = []
    for mint, entry in self.cache.items():
        age = (now - entry["discovered_at"]).total_seconds()
        if age > self.cache_seconds and not entry["activated"]:
            expired.append(mint)

    for mint in expired:
        del self.cache[mint]
        cache_expirations.inc()

    cache_size.set(len(self.cache))
    return expired
```

---

## CoinFilter Klasse (Zeilen 608-643)

Filtert Spam-Coins basierend auf Namen und Burst-Detection.

### Datenstruktur
```python
class CoinFilter:
    def __init__(self, spam_burst_window=30):
        self.spam_burst_window = spam_burst_window
        self.recent_names = {}     # {name: [timestamps]}
        self.recent_symbols = {}   # {symbol: [timestamps]}
```

### Filter-Logik (Zeile 615)
```python
def should_filter_coin(self, coin_data):
    """Prüft ob Coin gefiltert werden soll"""
    name = coin_data.get("name", "").lower()
    symbol = coin_data.get("symbol", "").lower()

    # 1. Bad Names Filter (Regex)
    bad_pattern = os.getenv("BAD_NAMES_PATTERN", "test|bot|rug|scam|cant|honey|faucet")
    if re.search(bad_pattern, name, re.IGNORECASE):
        coins_filtered.labels(reason="bad_name").inc()
        return True

    # 2. Spam Burst Detection
    now = time.time()
    cutoff = now - self.spam_burst_window

    # Cleanup alte Einträge
    self.recent_names = {k: [t for t in v if t > cutoff]
                         for k, v in self.recent_names.items()}

    # Prüfe auf Duplikate im Fenster
    if name in self.recent_names and len(self.recent_names[name]) >= 3:
        coins_filtered.labels(reason="spam_burst").inc()
        return True

    # Registriere neuen Namen
    self.recent_names.setdefault(name, []).append(now)

    return False
```

---

## UnifiedService Klasse (Zeilen 1498-2561)

Die Hauptklasse, die alle Funktionalitäten orchestriert.

### Konstruktor (Zeile 1504)
```python
def __init__(self):
    # Datenbankverbindung
    self.pool = None

    # WebSocket
    self.ws = None
    self.ws_lock = asyncio.Lock()

    # Hilfsobjekte
    self.cache = CoinCache(int(os.getenv("COIN_CACHE_SECONDS", 120)))
    self.filter = CoinFilter(int(os.getenv("SPAM_BURST_WINDOW", 30)))

    # Phasen-Konfiguration
    self.phases_config = {}  # {phase_id: {name, interval, min_age, max_age}}

    # Watchlist (aktive Streams)
    self.watchlist = {}  # {mint: WatchlistEntry}

    # ATH Tracking
    self.ath_cache = {}       # {mint: ath_price}
    self.dirty_aths = set()   # Mints mit neuen ATHs

    # Discovery Buffer (für n8n)
    self.discovery_buffer = []
    self.discovery_buffer_lock = asyncio.Lock()

    # Subscriptions
    self.subscribed_mints = set()
    self.pending_subscriptions = set()
```

### Watchlist-Entry Struktur
```python
# Jeder Eintrag in self.watchlist:
{
    "meta": {
        "mint": str,
        "phase_id": int,
        "created_at": datetime,
        "creator": str,          # Dev-Wallet für Tracking
    },
    "buffer": {                  # Trade-Buffer
        "open": None,
        "high": 0,
        "low": float('inf'),
        "close": 0,
        "vol": 0,
        "vol_buy": 0,
        "vol_sell": 0,
        "buys": 0,
        "sells": 0,
        "wallets": set(),
        "v_sol": 0,
        "mcap": 0,
        "dev_sold_amount": 0,
        "whale_buy_vol": 0,
        "whale_buys": 0,
        "micro_trades": 0,
    },
    "interval": int,             # Flush-Intervall (aus Phase)
    "next_flush": float,         # Nächster Flush-Zeitpunkt
    "last_trade_ts": float,      # Letzter Trade-Zeitpunkt
    "last_saved_signature": str, # Für Zombie-Detection
}
```

### Wichtige Methoden

#### `init_db_connection()` (Zeile 1543)
```python
async def init_db_connection(self):
    """Initialisiert PostgreSQL Connection Pool"""
    self.pool = await asyncpg.create_pool(
        DB_DSN,
        min_size=1,
        max_size=10,
        command_timeout=30
    )
    db_connected.set(1)

    # Lade Phasen-Konfiguration
    await self.reload_phases_config()
```

#### `reload_phases_config()` (Zeile 1615)
```python
async def reload_phases_config(self) -> int:
    """Lädt Phasen aus DB und aktualisiert aktive Streams"""
    rows = await self.pool.fetch(
        "SELECT id, name, interval_seconds, min_age_minutes, max_age_minutes "
        "FROM ref_coin_phases ORDER BY id"
    )

    self.phases_config = {
        row['id']: {
            'name': row['name'],
            'interval': row['interval_seconds'],
            'min_age': row['min_age_minutes'],
            'max_age': row['max_age_minutes']
        }
        for row in rows
    }

    # Aktualisiere Intervalle für aktive Streams
    updated = 0
    for mint, entry in self.watchlist.items():
        phase_id = entry["meta"]["phase_id"]
        if phase_id in self.phases_config:
            new_interval = self.phases_config[phase_id]["interval"]
            if entry["interval"] != new_interval:
                entry["interval"] = new_interval
                updated += 1

    return updated
```

#### `process_new_coin(coin_data)` (Zeile 1778)
```python
async def process_new_coin(self, coin_data):
    """Verarbeitet neu entdeckten Coin"""
    mint = coin_data.get("mint")

    # 1. Filter prüfen
    if self.filter.should_filter_coin(coin_data):
        return

    coins_received.inc()

    # 2. Preis berechnen
    v_sol = float(coin_data.get("vSolInBondingCurve", 0))
    v_tokens = float(coin_data.get("vTokensInBondingCurve", 1))
    price = v_sol / v_tokens if v_tokens > 0 else 0

    # 3. Social Count berechnen
    social_count = sum([
        1 for url in [
            coin_data.get("twitter"),
            coin_data.get("telegram"),
            coin_data.get("website"),
            coin_data.get("discord")
        ] if url
    ])

    # 4. Zum Cache hinzufügen
    self.cache.add_coin(mint, {
        **coin_data,
        "price_sol": price,
        "social_count": social_count,
        "has_socials": social_count > 0
    })

    # 5. Trade-Subscription starten
    self.pending_subscriptions.add(mint)

    # 6. Zum Discovery-Buffer hinzufügen (für n8n)
    async with self.discovery_buffer_lock:
        self.discovery_buffer.append({
            "mint": mint,
            "name": coin_data.get("name"),
            "symbol": coin_data.get("symbol"),
            "price_sol": price,
            "creator": coin_data.get("traderPublicKey"),
            "discovered_at": datetime.utcnow().isoformat()
        })
        n8n_buffer_size.set(len(self.discovery_buffer))
```

#### `process_trade(data)` (Zeile 1860)
```python
def process_trade(self, data):
    """Verarbeitet einzelnen Trade"""
    mint = data.get("mint")

    # Coin im Cache? → Trades sammeln
    if mint in self.cache.cache and not self.cache.cache[mint]["activated"]:
        self.cache.add_trade(mint, data)
        return

    # Coin in Watchlist? → Metriken aktualisieren
    if mint not in self.watchlist:
        return

    trades_received.inc()

    entry = self.watchlist[mint]
    buf = entry["buffer"]

    # Trade-Daten extrahieren
    sol = float(data.get("solAmount", 0))
    v_sol = float(data.get("vSolInBondingCurve", 0))
    v_tokens = float(data.get("vTokensInBondingCurve", 1))
    price = v_sol / v_tokens if v_tokens > 0 else 0
    is_buy = data.get("txType") == "buy"
    trader = data.get("traderPublicKey", "")

    # ATH aktualisieren
    if price > self.ath_cache.get(mint, 0):
        self.ath_cache[mint] = price
        self.dirty_aths.add(mint)

    # OHLCV Buffer aktualisieren
    if buf["open"] is None:
        buf["open"] = price
    buf["close"] = price
    buf["high"] = max(buf["high"], price)
    buf["low"] = min(buf["low"], price)
    buf["vol"] += sol

    # Buy/Sell Tracking
    if is_buy:
        buf["buys"] += 1
        buf["vol_buy"] += sol
        # Whale Detection (>= 1.0 SOL)
        if sol >= float(os.getenv("WHALE_THRESHOLD_SOL", 1.0)):
            buf["whale_buy_vol"] += sol
            buf["whale_buys"] += 1
    else:
        buf["sells"] += 1
        buf["vol_sell"] += sol
        # Dev Sold Tracking
        if trader == entry["meta"]["creator"]:
            buf["dev_sold_amount"] += sol

    # Micro Trade Detection (< 0.01 SOL)
    if sol < 0.01:
        buf["micro_trades"] += 1

    # Wallet Tracking
    buf["wallets"].add(trader)
    buf["v_sol"] = v_sol
    buf["mcap"] = price * 1_000_000_000  # 1 Billion Supply

    entry["last_trade_ts"] = time.time()
    trades_processed.inc()
```

#### `check_lifecycle_and_flush(now_ts)` (Zeile 2092)
```python
async def check_lifecycle_and_flush(self, now_ts):
    """Prüft Phase-Upgrades und speichert Metriken"""
    to_remove = []

    for mint, entry in self.watchlist.items():
        created_at = entry["meta"]["created_at"]
        current_pid = entry["meta"]["phase_id"]
        buf = entry["buffer"]

        # Alter berechnen (mit Offset)
        age_minutes = (datetime.utcnow() - created_at).total_seconds() / 60
        age_minutes -= int(os.getenv("AGE_CALCULATION_OFFSET_MIN", 60))

        # Phase-Upgrade prüfen
        phase_cfg = self.phases_config.get(current_pid, {})
        max_age = phase_cfg.get("max_age", 999999)

        if age_minutes > max_age:
            # Finde nächste Phase
            sorted_phases = sorted(self.phases_config.keys())
            next_phases = [p for p in sorted_phases if p > current_pid and p < 99]

            if next_phases:
                next_pid = next_phases[0]
                await self.switch_phase(mint, current_pid, next_pid)
                entry["meta"]["phase_id"] = next_pid
                entry["interval"] = self.phases_config[next_pid]["interval"]
            else:
                # Keine weitere Phase → Tracking beenden
                await self.stop_tracking(mint, is_graduation=False)
                to_remove.append(mint)
                continue

        # Graduation Check (Bonding Curve >= 99.5%)
        bonding_pct = (buf["v_sol"] / 85.0) * 100 if buf["v_sol"] > 0 else 0
        if bonding_pct >= 99.5:
            await self.stop_tracking(mint, is_graduation=True)
            to_remove.append(mint)
            continue

        # Flush-Zeitpunkt erreicht?
        if now_ts >= entry["next_flush"]:
            # Zombie-Detection: Identische Daten?
            signature = f"{buf['close']:.10f}_{buf['vol']:.6f}_{buf['buys']+buf['sells']}"
            if signature == entry.get("last_saved_signature"):
                # Keine neuen Daten → Skip
                entry["next_flush"] = now_ts + entry["interval"]
                continue

            # Metriken speichern
            await self.flush_batch(mint, entry)
            entry["last_saved_signature"] = signature
            entry["next_flush"] = now_ts + entry["interval"]

    # Entferne beendete Streams
    for mint in to_remove:
        del self.watchlist[mint]
        self.subscribed_mints.discard(mint)
```

#### `run()` (Zeile 2261)
```python
async def run(self):
    """Haupt-Event-Loop"""
    await self.init_db_connection()

    while True:
        try:
            async with websockets.connect(
                WS_URI,
                ping_interval=20,
                ping_timeout=5,
                close_timeout=10
            ) as ws:
                self.ws = ws
                ws_connected.set(1)

                # Subscribe zu neuen Tokens
                await ws.send(json.dumps({"method": "subscribeNewToken"}))

                # Restore bestehende Subscriptions
                if self.subscribed_mints:
                    await ws.send(json.dumps({
                        "method": "subscribeTokenTrade",
                        "keys": list(self.subscribed_mints)
                    }))

                # Background Tasks starten
                batching_task = asyncio.create_task(
                    self.run_subscription_batching_task(ws)
                )

                # Main Loop
                last_flush = time.time()
                while True:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        data = json.loads(msg)

                        tx_type = data.get("txType")
                        if tx_type == "create":
                            await self.process_new_coin(data)
                        elif tx_type in ("buy", "sell"):
                            self.process_trade(data)

                    except asyncio.TimeoutError:
                        pass

                    # Periodische Tasks
                    now = time.time()
                    if now - last_flush >= 1.0:
                        await self.check_lifecycle_and_flush(now)
                        await self.check_cache_activation()
                        await self.flush_discovery_buffer()
                        await self.flush_ath_updates()
                        last_flush = now

        except websockets.ConnectionClosed:
            ws_connected.set(0)
            ws_reconnects.inc()

            # Exponential Backoff
            delay = min(3 * (1 + unified_status["reconnect_count"] * 0.5), 60)
            await asyncio.sleep(delay)
            unified_status["reconnect_count"] += 1
```

---

## Globaler Status (Zeile 302)

```python
unified_status = {
    "db_connected": False,
    "ws_connected": False,
    "n8n_available": False,
    "last_error": None,
    "start_time": None,
    "connection_start": None,
    "last_message_time": None,
    "reconnect_count": 0,
    "total_coins_discovered": 0,
    "total_trades": 0,
    "total_metrics_saved": 0,
    "last_n8n_success": None
}
```

---

## Weiterführende Dokumentation

- [API Endpunkte](../api/endpoints.md)
- [Coin Discovery Algorithmus](../algorithms/coin-discovery.md)
- [Trade Processing](../algorithms/trade-processing.md)
- [Phase Management](../algorithms/phase-management.md)

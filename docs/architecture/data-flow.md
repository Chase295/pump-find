# Datenfluss im Detail

Dieses Dokument beschreibt den kompletten Datenfluss von der WebSocket-Verbindung bis zur Datenbank.

---

## Übersichts-Diagramm

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        pumpportal.fun WebSocket                              │
│                    wss://pumpportal.fun/api/data                             │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                   ┌────────────┴────────────┐
                   │                         │
            "create" Event            "buy/sell" Event
            (Neuer Token)              (Trade)
                   │                         │
                   ▼                         │
┌──────────────────────────────┐             │
│        CoinFilter            │             │
│  ┌────────────────────────┐  │             │
│  │  Bad Names Check       │  │             │
│  │  (Regex Pattern)       │  │             │
│  └────────────────────────┘  │             │
│  ┌────────────────────────┐  │             │
│  │  Spam Burst Check      │  │             │
│  │  (30s Window)          │  │             │
│  └────────────────────────┘  │             │
└───────────────┬──────────────┘             │
                │                            │
        Gefiltert? ──Yes──► 🚫 Verworfen     │
                │                            │
               No                            │
                │                            │
                ▼                            │
┌──────────────────────────────┐             │
│        process_new_coin()    │             │
│  ┌────────────────────────┐  │             │
│  │  Preis berechnen       │  │             │
│  │  price = mcap/tokens   │  │             │
│  └────────────────────────┘  │             │
│  ┌────────────────────────┐  │             │
│  │  Social Count          │  │             │
│  │  (Twitter, TG, etc.)   │  │             │
│  └────────────────────────┘  │             │
└───────────────┬──────────────┘             │
                │                            │
                ▼                            │
┌──────────────────────────────┐             │
│         CoinCache            │             │
│    (120 Sekunden TTL)        │             │
│  ┌────────────────────────┐  │             │
│  │  add_coin(mint, data)  │  │             │
│  │  trade_count: 0        │  │             │
│  │  activated: false      │  │             │
│  └────────────────────────┘  │             │
└───────────────┬──────────────┘             │
                │                            │
                ├──────────────────────────► │
                │                            │
                ▼                            ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│   pending_subscriptions      │  │      process_trade()         │
│   (Mint-Adressen Set)        │  │                              │
└───────────────┬──────────────┘  │  Coin in Cache?              │
                │                 │      │                       │
                ▼                 │     Yes                      │
     WebSocket Subscribe:        │      │                       │
     {"method":"subscribeTokenTrade", │  ▼                       │
      "keys": [...]}             │  cache.add_trade(mint)       │
                                 │  trade_count++               │
                                 │                              │
                                 │  trade_count >= 3?           │
                                 │      │                       │
                                 │     Yes                      │
                                 │      │                       │
                                 │      ▼                       │
                                 │  activate_coin(mint)         │
                                 │  ┌────────────────────────┐  │
                                 │  │  INSERT discovered_coins│  │
                                 │  │  INSERT coin_streams    │  │
                                 │  │  Add to watchlist       │  │
                                 │  └────────────────────────┘  │
                                 └───────────────┬──────────────┘
                                                 │
                                                 │
                ┌────────────────────────────────┤
                │                                │
                ▼                                ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│     Discovery Buffer         │  │         Watchlist            │
│   (Batch für n8n)            │  │    (Aktive Streams)          │
│  ┌────────────────────────┐  │  │  ┌────────────────────────┐  │
│  │  Max 10 Coins oder     │  │  │  │  mint → {              │  │
│  │  30s Timeout           │  │  │  │    meta: {...},        │  │
│  └────────────────────────┘  │  │  │    buffer: {OHLCV},    │  │
└───────────────┬──────────────┘  │  │    interval: 5s,       │  │
                │                 │  │    next_flush: ts       │  │
                ▼                 │  │  }                      │  │
┌──────────────────────────────┐  │  └────────────────────────┘  │
│     n8n Webhook              │  └───────────────┬──────────────┘
│   POST /webhook/endpoint     │                  │
│  ┌────────────────────────┐  │                  │
│  │  Batch von Coins       │  │           Weitere Trades
│  │  mit allen Metadaten   │  │                  │
│  └────────────────────────┘  │                  ▼
└──────────────────────────────┘  ┌──────────────────────────────┐
                                  │      process_trade()         │
                                  │  ┌────────────────────────┐  │
                                  │  │  OHLCV Update          │  │
                                  │  │  Whale Detection       │  │
                                  │  │  Dev Tracking          │  │
                                  │  │  ATH Update            │  │
                                  │  └────────────────────────┘  │
                                  └───────────────┬──────────────┘
                                                  │
                                           Interval erreicht?
                                                  │
                                                 Yes
                                                  │
                                                  ▼
                                  ┌──────────────────────────────┐
                                  │   check_lifecycle_and_flush()│
                                  │  ┌────────────────────────┐  │
                                  │  │  INSERT coin_metrics   │  │
                                  │  │  Phase-Upgrade prüfen  │  │
                                  │  │  Graduation prüfen     │  │
                                  │  │  Buffer zurücksetzen   │  │
                                  │  └────────────────────────┘  │
                                  └───────────────┬──────────────┘
                                                  │
                                                  ▼
                                  ┌──────────────────────────────┐
                                  │        PostgreSQL            │
                                  │  ┌────────────────────────┐  │
                                  │  │  discovered_coins      │  │
                                  │  │  coin_streams          │  │
                                  │  │  coin_metrics          │  │
                                  │  │  ref_coin_phases       │  │
                                  │  └────────────────────────┘  │
                                  └──────────────────────────────┘
```

---

## Schritt-für-Schritt Erklärung

### 1. WebSocket Verbindung

```python
# unified_service.py Zeile 2331-2350
async def run(self):
    while True:
        try:
            async with connect(WS_URI, ping_interval=20, ping_timeout=10) as ws:
                unified_status["ws_connected"] = True
                ws_connected.set(1)

                # Neuen Token-Stream abonnieren
                await ws.send(json.dumps({
                    "method": "subscribeNewToken"
                }))
```

**Was passiert:**
- Verbindung zu `wss://pumpportal.fun/api/data`
- Ping alle 20 Sekunden, Timeout nach 10 Sekunden
- Sofortiges Abonnieren des `subscribeNewToken` Events

### 2. Event-Routing (Zeile 2393-2414)

```python
async for message in ws:
    msg = json.loads(message)

    # Neuer Token (create Event)
    if msg.get("txType") == "create":
        await self.process_new_coin(msg)

    # Trade (buy/sell Event)
    elif msg.get("txType") in ("buy", "sell"):
        mint = msg.get("mint")

        # Erst Cache-Trade prüfen
        if mint in self.coin_cache.cache:
            self.coin_cache.add_trade(mint)
            if self.coin_cache.should_activate(mint):
                await self.activate_coin(mint)

        # Dann aktiven Stream prüfen
        if mint in self.watchlist:
            self.process_trade(msg)
```

### 3. CoinFilter (Zeile 608-643)

```python
def should_filter_coin(self, coin_data):
    name = coin_data.get("name", "").lower()
    symbol = coin_data.get("symbol", "").lower()

    # Bad Names Regex
    if self.bad_names_pattern.search(name) or \
       self.bad_names_pattern.search(symbol):
        return True, "bad_name"

    # Spam Burst Detection (>5 Coins in 30s vom selben Dev)
    creator = coin_data.get("traderPublicKey", "")
    now = time.time()

    self.creator_timestamps[creator].append(now)
    # Nur Timestamps der letzten 30s behalten
    recent = [t for t in self.creator_timestamps[creator]
              if now - t < 30]

    if len(recent) > 5:
        return True, "spam_burst"

    return False, None
```

### 4. process_new_coin (Zeile 1778-1822)

```python
async def process_new_coin(self, coin_data):
    mint = coin_data.get("mint")

    # 1. Filter anwenden
    should_filter, reason = self.coin_filter.should_filter_coin(coin_data)
    if should_filter:
        return

    # 2. Preis berechnen
    v_tokens = coin_data.get("vTokensInBondingCurve", 0)
    market_cap = coin_data.get("marketCapSol", 0)
    price_sol = market_cap / v_tokens if v_tokens > 0 else 0

    # 3. Social Count
    social_count = 0
    if coin_data.get("twitter_url"): social_count += 1
    if coin_data.get("telegram_url"): social_count += 1
    # etc.

    # 4. In Cache legen
    self.coin_cache.add_coin(mint, coin_data)

    # 5. Für Trades abonnieren
    self.pending_subscriptions.add(mint)

    # 6. In Discovery-Buffer für n8n
    self.discovery_buffer.append(coin_data)
```

### 5. CoinCache System (Zeile 505-605)

```python
class CoinCache:
    def __init__(self, ttl_seconds=120):
        self.ttl = ttl_seconds
        self.cache = {}  # mint → CacheEntry

    def add_coin(self, mint, data):
        self.cache[mint] = {
            "data": data,
            "trade_count": 0,
            "activated": False,
            "created_at": time.time()
        }

    def add_trade(self, mint):
        if mint in self.cache:
            self.cache[mint]["trade_count"] += 1

    def should_activate(self, mint):
        entry = self.cache.get(mint)
        if not entry or entry["activated"]:
            return False
        return entry["trade_count"] >= 3

    def cleanup_expired(self):
        now = time.time()
        expired = [m for m, e in self.cache.items()
                   if now - e["created_at"] > self.ttl]
        for mint in expired:
            del self.cache[mint]
```

**Warum 120 Sekunden und 3 Trades?**
- Filtert Tokens ohne echte Aktivität
- Spart Datenbankressourcen
- Verhindert Tracking von "Dead on Arrival" Tokens

### 6. activate_coin (Zeile 1735-1775)

```python
async def activate_coin(self, mint):
    cached = self.coin_cache.cache.get(mint)
    if not cached or cached["activated"]:
        return

    cached["activated"] = True
    coin_data = cached["data"]

    # 1. In discovered_coins speichern
    await self.db_pool.execute("""
        INSERT INTO discovered_coins (token_address, name, symbol, ...)
        VALUES ($1, $2, $3, ...)
        ON CONFLICT (token_address) DO NOTHING
    """, mint, coin_data["name"], coin_data["symbol"], ...)

    # 2. Stream anlegen
    await self.db_pool.execute("""
        INSERT INTO coin_streams (token_address, current_phase_id, is_active)
        VALUES ($1, 1, true)
    """, mint)

    # 3. In Watchlist aufnehmen
    self.add_to_watchlist(mint, coin_data, phase_id=1)
```

### 7. Discovery Buffer → n8n (Zeile 1824-1846)

```python
async def flush_discovery_buffer(self):
    if not self.discovery_buffer:
        return

    # Trigger: 10 Coins ODER 30 Sekunden
    is_full = len(self.discovery_buffer) >= BATCH_SIZE  # 10
    is_timeout = (time.time() - self.last_flush) > BATCH_TIMEOUT  # 30s

    if is_full or is_timeout:
        success = await send_batch_to_n8n(self.discovery_buffer)

        if success:
            # Markiere als gesendet
            for coin in self.discovery_buffer:
                self.coin_cache.cache[coin["mint"]]["n8n_sent"] = True

            self.discovery_buffer = []
```

### 8. process_trade (Zeile 1860-1920)

```python
def process_trade(self, data):
    mint = data["mint"]
    entry = self.watchlist[mint]
    buf = entry["buffer"]

    # Trade-Daten extrahieren
    sol = float(data["solAmount"])
    price = float(data["vSolInBondingCurve"]) / float(data["vTokensInBondingCurve"])
    is_buy = data["txType"] == "buy"
    trader = data.get("traderPublicKey", "")

    # OHLCV Update
    if buf["open"] is None:
        buf["open"] = price
    buf["close"] = price
    buf["high"] = max(buf["high"], price)
    buf["low"] = min(buf["low"], price)
    buf["vol"] += sol

    # Buy/Sell Stats
    if is_buy:
        buf["buys"] += 1
        buf["vol_buy"] += sol
        # Whale Check (>= 1.0 SOL)
        if sol >= 1.0:
            buf["whale_buys"] += 1
            buf["whale_buy_vol"] += sol
    else:
        buf["sells"] += 1
        buf["vol_sell"] += sol
        # Dev Tracking
        if trader == entry["meta"]["creator_address"]:
            buf["dev_sold_amount"] += sol

    # Micro Trade Check (< 0.01 SOL)
    if sol < 0.01:
        buf["micro_trades"] += 1

    # Unique Wallets
    buf["wallets"].add(trader)

    # ATH Update
    if price > self.ath_cache.get(mint, 0):
        self.ath_cache[mint] = price
        self.dirty_aths.add(mint)
```

### 9. check_lifecycle_and_flush (Zeile 1980-2080)

```python
async def check_lifecycle_and_flush(self):
    now_ts = time.time()
    mints_to_flush = []

    for mint, entry in self.watchlist.items():
        # Zeit für Flush?
        if now_ts >= entry["next_flush"]:
            mints_to_flush.append(mint)

    if not mints_to_flush:
        return

    # Batch-Insert vorbereiten
    rows = []
    for mint in mints_to_flush:
        entry = self.watchlist[mint]
        buf = entry["buffer"]

        # Keine Trades? Skip
        if buf["open"] is None:
            continue

        rows.append((
            mint,
            now_ts,
            buf["open"], buf["high"], buf["low"], buf["close"],
            buf["vol"], buf["vol_buy"], buf["vol_sell"],
            buf["buys"], buf["sells"],
            len(buf["wallets"]),
            buf["whale_buys"], buf["whale_sells"],
            buf["whale_buy_vol"], buf["whale_sell_vol"],
            buf["dev_sold_amount"],
            buf["micro_trades"],
            buf["mcap"]
        ))

        # Buffer zurücksetzen
        entry["buffer"] = self.get_empty_buffer()
        entry["next_flush"] = now_ts + entry["interval"]

        # Phase-Upgrade prüfen
        await self.check_phase_upgrade(mint, entry)

    # Batch-Insert
    if rows:
        await self.db_pool.executemany("""
            INSERT INTO coin_metrics (mint, timestamp, ...)
            VALUES ($1, $2, ...)
        """, rows)
```

### 10. Phase-Upgrade (Zeile 2090-2150)

```python
async def check_phase_upgrade(self, mint, entry):
    age_minutes = (time.time() - entry["meta"]["started_at"]) / 60
    current_phase = entry["phase_id"]

    # Phase-Definition laden
    phase = self.phases_config[current_phase]

    # Zu alt für aktuelle Phase?
    if age_minutes > phase["max_age_minutes"]:
        # Nächste Phase finden
        next_phase = self.find_next_phase(current_phase, age_minutes)

        if next_phase:
            # Upgrade durchführen
            await self.db_pool.execute("""
                UPDATE coin_streams
                SET current_phase_id = $1
                WHERE token_address = $2
            """, next_phase, mint)

            entry["phase_id"] = next_phase
            entry["interval"] = self.phases_config[next_phase]["interval_seconds"]
        else:
            # Keine passende Phase → Finished (99)
            await self.deactivate_stream(mint, phase_id=99)
```

---

## Zeitliches Ablaufdiagramm

```
Zeit    Event                          Aktion
────────────────────────────────────────────────────────────────
t=0     WebSocket: create Event        → CoinFilter prüft
t=0.1   Filter passed                  → add_coin() in Cache
t=0.2   Subscribe Token Trades         → WebSocket Subscribe
t=0.5   Trade #1                       → cache.add_trade()
t=1.2   Trade #2                       → cache.add_trade()
t=2.0   Trade #3                       → should_activate() = true
t=2.1   activate_coin()                → INSERT discovered_coins
                                       → INSERT coin_streams
                                       → Add to watchlist
t=2.2   Trade #4                       → process_trade() → Buffer
t=3.5   Trade #5                       → process_trade() → Buffer
t=5.0   Phase 1 Interval (5s)          → check_lifecycle_and_flush()
                                       → INSERT coin_metrics
                                       → Reset Buffer
t=10.0  Phase 1 Interval (5s)          → Flush #2
...
t=600   age > max_age (10 min)         → Phase Upgrade 1 → 2
                                       → Interval: 5s → 15s
t=7200  age > max_age (120 min)        → Phase Upgrade 2 → 3
t=14400 age > max_age (240 min)        → Finished (Phase 99)
                                       → is_active = false
```

---

## Datenbank-Operationen

### INSERT-Sequenz bei Coin-Aktivierung

```sql
-- 1. Coin speichern
INSERT INTO discovered_coins (
    token_address, name, symbol, price_sol, market_cap_sol,
    pool_address, creator_address, social_count, has_socials,
    twitter_url, telegram_url, website_url, ...
) VALUES ($1, $2, $3, ...)
ON CONFLICT (token_address) DO NOTHING;

-- 2. Stream anlegen
INSERT INTO coin_streams (
    token_address, current_phase_id, is_active, started_at
) VALUES ($1, 1, true, NOW());
```

### INSERT-Sequenz bei Metrics-Flush

```sql
INSERT INTO coin_metrics (
    mint, timestamp,
    price_open, price_high, price_low, price_close,
    volume_sol, volume_buy_sol, volume_sell_sol,
    num_buys, num_sells, unique_wallets,
    whale_buys, whale_sells, whale_buy_volume, whale_sell_volume,
    dev_sold_sol, micro_trades, market_cap_sol
) VALUES ($1, $2, $3, ...);
```

### UPDATE-Sequenz bei Phase-Upgrade

```sql
UPDATE coin_streams
SET current_phase_id = $1, updated_at = NOW()
WHERE token_address = $2;
```

---

## Fehlerbehandlung

### WebSocket Reconnect

```python
# Exponential Backoff bei Verbindungsverlust
reconnect_delay = 1  # Start: 1 Sekunde
max_delay = 60       # Max: 60 Sekunden

while True:
    try:
        async with connect(WS_URI) as ws:
            reconnect_delay = 1  # Reset bei Erfolg
            # ... Normal Operation
    except Exception as e:
        await asyncio.sleep(reconnect_delay)
        reconnect_delay = min(reconnect_delay * 2, max_delay)
```

### Database Connection Pool

```python
# Connection Pool mit Retry
self.db_pool = await asyncpg.create_pool(
    DB_DSN,
    min_size=5,
    max_size=20,
    command_timeout=30
)
```

---

## Weiterführende Dokumentation

- [Backend-Architektur](backend.md) - Detaillierte Klassen-Dokumentation
- [API-Endpunkte](../api/endpoints.md) - REST API Referenz
- [Phase Management](../algorithms/phase-management.md) - Lifecycle im Detail

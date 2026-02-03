# Coin Discovery Algorithmus

Dokumentation des Token-Entdeckungs- und Filtermechanismus.

---

## Übersicht

```
WebSocket (create Event)
         │
         ▼
┌─────────────────────┐
│     CoinFilter      │
│  ┌───────────────┐  │
│  │ Bad Names     │──► Gefiltert (bad_name)
│  └───────────────┘  │
│  ┌───────────────┐  │
│  │ Spam Burst    │──► Gefiltert (spam_burst)
│  └───────────────┘  │
└─────────┬───────────┘
          │
         OK
          │
          ▼
┌─────────────────────┐
│  process_new_coin() │
│  - Preis berechnen  │
│  - Social Count     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│     CoinCache       │
│  (120 Sekunden TTL) │
│  - Trades sammeln   │
│  - Aktivierung      │
└─────────┬───────────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
Discovery   Aktivierung
Buffer      (>= 3 Trades)
    │           │
    ▼           ▼
  n8n        Database
Webhook    Insert + Stream
```

---

## CoinFilter Klasse

**Code-Referenz:** `unified_service.py:608-643`

### Initialisierung

```python
class CoinFilter:
    def __init__(self, spam_burst_window=30):
        self.recent_coins = []  # [(timestamp, name, symbol), ...]
        self.spam_burst_window = spam_burst_window  # Default: 30 Sekunden
```

### Bad Names Filter

**Konfiguration:**
```python
# unified_service.py:133-134
BAD_NAMES_PATTERN = "test|bot|rug|scam|cant|honey|faucet"
BAD_NAMES = re.compile(rf'({BAD_NAMES_PATTERN})', re.IGNORECASE)
```

**Standard-Pattern:**

| Pattern | Filtert | Grund |
|---------|---------|-------|
| `test` | "TestCoin", "testing" | Test-Tokens |
| `bot` | "BotToken", "robot" | Bot-generiert |
| `rug` | "RugPull", "NotARug" | Rug-Pull Risiko |
| `scam` | "ScamCoin", "NoScam" | Scam-Verdacht |
| `cant` | "CantLose" | Verdächtige Namen |
| `honey` | "HoneyPot" | Honeypot-Risiko |
| `faucet` | "FreeFaucet" | Faucet-Tokens |

**Filter-Logik:**
```python
def should_filter_coin(self, coin_data):
    name = coin_data.get("name", "").strip()
    symbol = coin_data.get("symbol", "").strip()

    # Bad Names prüfen (case-insensitive)
    if BAD_NAMES.search(name):
        coins_filtered.labels(reason="bad_name").inc()
        return True, "bad_name"
```

**Anpassung:**
```bash
# Via Environment Variable
BAD_NAMES_PATTERN=test|bot|rug|scam|spam

# Via API
curl -X PUT http://localhost:3001/api/config \
  -H "Content-Type: application/json" \
  -d '{"bad_names_pattern": "test|bot|rug|scam|spam|airdrop"}'
```

### Spam Burst Filter

**Zweck:** Erkennt wenn dasselbe Token mehrfach in kurzer Zeit erstellt wird (Bot-Spam).

```python
# Spam-Burst Detection
now = time.time()
recent_identical = [
    ts for ts, n, s in self.recent_coins
    if (n == name or s == symbol) and (now - ts) < self.spam_burst_window
]

if recent_identical:
    coins_filtered.labels(reason="spam_burst").inc()
    return True, "spam_burst"
```

**Mechanismus:**
1. Jeder passierte Coin wird mit Timestamp in `recent_coins` gespeichert
2. Bei neuem Coin: Prüfe ob Name oder Symbol in letzten X Sekunden vorkam
3. Wenn ja → Spam-Burst, Token filtern
4. Liste wird bei 2x Window-Größe aufgeräumt

**Konfiguration:**
```python
SPAM_BURST_WINDOW = 30  # Sekunden (Default)

# Via API ändern
curl -X PUT http://localhost:3001/api/config \
  -H "Content-Type: application/json" \
  -d '{"spam_burst_window": 60}'
```

**Beispiel-Szenario:**
```
t=0:   Token "MoonCoin" (MOON) → OK, gespeichert
t=5:   Token "MoonCoin" (MOON) → Spam-Burst! (gefiltert)
t=10:  Token "MoonCoin2" (MOON) → Spam-Burst! (Symbol MOON in 30s)
t=35:  Token "MoonCoin" (MOON) → OK (31 Sekunden vergangen)
```

### Memory Cleanup

```python
# Alte Einträge entfernen (älter als 2x Window)
cutoff = now - (self.spam_burst_window * 2)
self.recent_coins = [(ts, n, s) for ts, n, s in self.recent_coins if ts > cutoff]
```

---

## CoinCache Klasse

**Code-Referenz:** `unified_service.py:506-605`

### Zweck

Der Cache dient als "Validierungs-Zone" für neue Tokens:
- Sammelt Trades während der ersten 120 Sekunden
- Aktiviert Coins erst nach >= 3 Trades (echte Aktivität)
- Verhindert Tracking von "Dead on Arrival" Tokens

### Datenstruktur

```python
self.cache = {
    "mint123...": {
        "discovered_at": 1705000000.0,       # Unix Timestamp
        "metadata": {                         # Komplette Coin-Daten
            "name": "Example Token",
            "symbol": "EX",
            "price_sol": 0.00001234,
            ...
        },
        "trades": [                           # Gesammelte Trades
            (1705000001.0, {trade_data}),
            (1705000005.0, {trade_data}),
            ...
        ],
        "n8n_sent": False,                    # An n8n gesendet?
        "activated": False,                   # Für Tracking aktiviert?
        "subscription_active": True           # Trade-Subscription aktiv?
    }
}
```

### add_coin()

```python
def add_coin(self, mint, coin_data):
    """Fügt neuen Coin zum Cache hinzu"""
    now = time.time()
    self.cache[mint] = {
        "discovered_at": now,
        "metadata": coin_data.copy(),
        "trades": [],
        "n8n_sent": False,
        "activated": False,
        "subscription_active": True
    }
    cache_size.set(len(self.cache))
    print(f"🆕 Coin {mint[:8]}... in {self.cache_seconds}s Cache gelegt")
```

### add_trade()

```python
def add_trade(self, mint, trade_data):
    """Fügt Trade zu Cache hinzu (falls Coin noch nicht aktiv)"""
    if mint in self.cache and not self.cache[mint]["activated"]:
        now = time.time()
        self.cache[mint]["trades"].append((now, trade_data))
```

### activate_coin()

```python
def activate_coin(self, mint, stream_data=None):
    """Aktiviert Coin für Tracking"""
    if mint in self.cache:
        self.cache[mint]["activated"] = True
        trades = self.cache[mint]["trades"].copy()

        cache_size.set(len(self.cache))
        cache_activations.inc()
        print(f"✅ Coin {mint[:8]}... aktiviert - {len(trades)} Cache-Trades")

        return trades  # Gesammelte Trades für Replay
    return []
```

### cleanup_expired_coins()

```python
def cleanup_expired_coins(self, current_time=None):
    """Entfernt abgelaufene Coins aus dem Cache"""
    if current_time is None:
        current_time = time.time()

    expired_mints = []
    for mint, data in self.cache.items():
        age = current_time - data["discovered_at"]
        if age > self.cache_seconds and not data["activated"]:
            expired_mints.append(mint)

    for mint in expired_mints:
        self.remove_coin(mint)

    return len(expired_mints)
```

### get_cache_stats()

```python
def get_cache_stats(self):
    """Gibt Cache-Statistiken zurück"""
    total_coins = len(self.cache)
    activated_coins = sum(1 for data in self.cache.values() if data["activated"])
    expired_coins = total_coins - activated_coins

    oldest_age = min(time.time() - data["discovered_at"] for data in self.cache.values())
    newest_age = max(time.time() - data["discovered_at"] for data in self.cache.values())

    return {
        "total_coins": total_coins,
        "activated_coins": activated_coins,
        "expired_coins": expired_coins,
        "oldest_age_seconds": int(oldest_age),
        "newest_age_seconds": int(newest_age)
    }
```

---

## process_new_coin()

**Code-Referenz:** `unified_service.py:1778-1822`

### Ablauf

```python
async def process_new_coin(self, coin_data):
    mint = coin_data.get("mint")
    if not mint:
        return

    # 1. Filter anwenden
    should_filter, reason = self.coin_filter.should_filter_coin(coin_data)
    if should_filter:
        print(f"🚫 Coin {coin_data.get('symbol')} gefiltert: {reason}")
        return

    # 2. Preis berechnen
    v_tokens = coin_data.get("vTokensInBondingCurve", 0)
    market_cap = coin_data.get("marketCapSol", 0)
    price_sol = market_cap / v_tokens if v_tokens > 0 else 0

    # 3. Social Count berechnen
    social_count = 0
    if coin_data.get("twitter_url") or coin_data.get("twitter"):
        social_count += 1
    if coin_data.get("telegram_url") or coin_data.get("telegram"):
        social_count += 1
    if coin_data.get("website_url") or coin_data.get("website"):
        social_count += 1
    if coin_data.get("discord_url") or coin_data.get("discord"):
        social_count += 1

    # 4. Daten erweitern
    coin_data["price_sol"] = price_sol
    coin_data["pool_address"] = coin_data.get("bondingCurveKey", "")
    coin_data["social_count"] = social_count

    # 5. In Cache legen
    self.coin_cache.add_coin(mint, coin_data)

    # 6. Für Trades abonnieren
    self.pending_subscriptions.add(mint)

    # 7. An Discovery-Buffer für n8n
    self.discovery_buffer.append(coin_data)
    n8n_buffer_size.set(len(self.discovery_buffer))

    # 8. Statistiken aktualisieren
    unified_status["total_coins_discovered"] += 1
    coins_received.inc()

    print(f"➕ Neuer Coin: {coin_data.get('symbol')} (Cache: {len(self.coin_cache.cache)})")
```

---

## Discovery Buffer → n8n

**Code-Referenz:** `unified_service.py:1824-1846`

### Batching-Logik

```python
async def flush_discovery_buffer(self):
    """Sendet Discovery-Buffer an n8n"""
    if not self.discovery_buffer:
        return

    # Trigger: 10 Coins ODER 30 Sekunden seit letztem Flush
    is_full = len(self.discovery_buffer) >= BATCH_SIZE      # Default: 10
    is_timeout = (time.time() - self.last_discovery_flush) > BATCH_TIMEOUT  # Default: 30s

    if is_full or is_timeout:
        print(f"🚚 Sende {len(self.discovery_buffer)} Coins an n8n...")
        success = await send_batch_to_n8n(self.discovery_buffer)

        if success:
            # Markiere Coins als an n8n gesendet
            for coin in self.discovery_buffer:
                mint = coin.get("mint")
                if mint in self.coin_cache.cache:
                    self.coin_cache.cache[mint]["n8n_sent"] = True

            self.discovery_buffer = []
            n8n_buffer_size.set(0)
            buffer_size.set(0)

        self.last_discovery_flush = time.time()
```

### n8n Webhook

```python
async def send_batch_to_n8n(coins):
    """Sendet Coin-Batch an n8n Webhook"""
    if not N8N_WEBHOOK_URL:
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if N8N_WEBHOOK_METHOD == "POST":
                response = await client.post(N8N_WEBHOOK_URL, json=coins)
            else:
                response = await client.get(N8N_WEBHOOK_URL, params={"coins": json.dumps(coins)})

            if response.status_code in [200, 201, 202]:
                coins_sent_n8n.inc(len(coins))
                unified_status["n8n_available"] = True
                unified_status["last_n8n_success"] = time.time()
                return True

    except Exception as e:
        print(f"⚠️ n8n Error: {e}")
        unified_status["n8n_available"] = False

    return False
```

---

## Aktivierungs-Logik

**Code-Referenz:** `unified_service.py:2353` und `unified_service.py:1735-1775`

### check_cache_activation()

```python
async def check_cache_activation(self):
    """Prüft Cache auf zu aktivierende Coins"""
    activated_count = 0
    expired_count = 0

    for mint in list(self.coin_cache.cache.keys()):
        entry = self.coin_cache.cache[mint]

        # Schon aktiviert? Skip
        if entry["activated"]:
            continue

        # Genug Trades für Aktivierung?
        if len(entry["trades"]) >= 3:
            await self.activate_coin(mint)
            activated_count += 1

    # Abgelaufene Coins entfernen
    expired_count = self.coin_cache.cleanup_expired_coins()

    return activated_count, expired_count
```

### activate_coin()

```python
async def activate_coin(self, mint):
    """Aktiviert Coin und startet Tracking"""
    cached = self.coin_cache.cache.get(mint)
    if not cached or cached["activated"]:
        return

    cached["activated"] = True
    coin_data = cached["metadata"]

    # 1. In discovered_coins speichern
    await self.pool.execute("""
        INSERT INTO discovered_coins (
            token_address, name, symbol, price_sol, market_cap_sol,
            pool_address, creator_address, social_count, has_socials,
            twitter_url, telegram_url, website_url, ...
        ) VALUES ($1, $2, $3, ...)
        ON CONFLICT (token_address) DO NOTHING
    """, mint, coin_data["name"], ...)

    # 2. Stream anlegen
    await self.pool.execute("""
        INSERT INTO coin_streams (token_address, current_phase_id, is_active)
        VALUES ($1, 1, true)
    """, mint)

    # 3. In Watchlist aufnehmen
    self.add_to_watchlist(mint, coin_data, phase_id=1)

    # 4. Gesammelte Trades verarbeiten
    cached_trades = cached["trades"]
    for ts, trade_data in cached_trades:
        self.process_trade(trade_data)

    print(f"✅ Coin {mint[:8]}... aktiviert mit {len(cached_trades)} Cache-Trades")
```

---

## Prometheus Metriken

| Metrik | Typ | Beschreibung |
|--------|-----|--------------|
| `unified_coins_received_total` | Counter | Alle empfangenen Coins |
| `unified_coins_filtered_total` | Counter | Gefilterte Coins (Labels: reason) |
| `unified_coins_sent_n8n_total` | Counter | An n8n gesendete Coins |
| `unified_cache_size` | Gauge | Aktuelle Cache-Größe |
| `unified_cache_activations_total` | Counter | Cache-Aktivierungen |
| `unified_cache_expirations_total` | Counter | Cache-Expirations |
| `unified_n8n_buffer_size` | Gauge | Discovery-Buffer-Größe |

---

## Konfigurationsparameter

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `COIN_CACHE_SECONDS` | 120 | Cache-TTL in Sekunden |
| `BATCH_SIZE` | 10 | Coins pro n8n-Batch |
| `BATCH_TIMEOUT` | 30 | Max. Wartezeit für Batch (Sekunden) |
| `BAD_NAMES_PATTERN` | `test\|bot\|...` | Regex für Bad Names |
| `SPAM_BURST_WINDOW` | 30 | Spam-Burst-Fenster (Sekunden) |

---

## Weiterführende Dokumentation

- [Trade Processing](trade-processing.md) - Was nach Aktivierung passiert
- [WebSocket-Protokoll](../api/websocket.md) - Event-Format
- [Datenfluss](../architecture/data-flow.md) - Gesamtübersicht

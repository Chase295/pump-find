# WebSocket-Protokoll

Dokumentation der WebSocket-Verbindung zu pumpportal.fun für Echtzeit-Token-Daten.

---

## Verbindungsdetails

| Parameter | Wert |
|-----------|------|
| **URL** | `wss://pumpportal.fun/api/data` |
| **Ping-Intervall** | 20 Sekunden |
| **Ping-Timeout** | 10 Sekunden |
| **Connection-Timeout** | 300 Sekunden (5 Minuten) |

**Code-Referenz:** `unified_service.py:2280-2300`

---

## Verbindungsaufbau

```python
async with connect(
    WS_URI,
    ping_interval=20,
    ping_timeout=10
) as ws:
    # 1. Neue Token abonnieren
    await ws.send(json.dumps({"method": "subscribeNewToken"}))

    # 2. Bestehende aktive Coins abonnieren
    if self.subscribed_mints:
        await ws.send(json.dumps({
            "method": "subscribeTokenTrade",
            "keys": list(self.subscribed_mints)
        }))
```

---

## Subscription-Methoden

### subscribeNewToken

**Zweck:** Benachrichtigung über neue Token-Erstellungen

**Request:**
```json
{
  "method": "subscribeNewToken"
}
```

**Events:** Empfängt `create` Events für alle neuen Tokens

---

### subscribeTokenTrade

**Zweck:** Trade-Events für spezifische Tokens abonnieren

**Request:**
```json
{
  "method": "subscribeTokenTrade",
  "keys": ["So11111...", "Abc2222...", "Xyz3333..."]
}
```

**Parameter:**
- `keys` (array): Liste von Token-Adressen (Mint-Adressen)

**Batching:** Das System verwendet Batch-Subscriptions alle 2 Sekunden mit maximal 50 Tokens pro Batch.

```python
# unified_service.py:2007-2049
async def run_subscription_batching_task(self, ws):
    batch_interval = 2.0
    max_batch_size = 50

    while True:
        await asyncio.sleep(batch_interval)

        if self.pending_subscriptions:
            batch_mints = list(self.pending_subscriptions)[:max_batch_size]
            await ws.send(json.dumps({
                "method": "subscribeTokenTrade",
                "keys": batch_mints
            }))
```

---

### unsubscribeTokenTrade

**Zweck:** Trade-Events für spezifische Tokens abbestellen

**Request:**
```json
{
  "method": "unsubscribeTokenTrade",
  "keys": ["So11111..."]
}
```

**Verwendung:** Bei Force-Resubscribe (Zombie Detection)

```python
# Erst unsubscribe, dann neu subscribe
unsubscribe_msg = {"method": "unsubscribeTokenTrade", "keys": [mint]}
await ws.send(json.dumps(unsubscribe_msg))

# Kurze Pause
await asyncio.sleep(0.5)

# Neu abonnieren
subscribe_msg = {"method": "subscribeTokenTrade", "keys": [mint]}
await ws.send(json.dumps(subscribe_msg))
```

---

## Event-Typen

### create Event (Neuer Token)

**Trigger:** Token wird auf pump.fun erstellt

**Beispiel-Payload:**
```json
{
  "txType": "create",
  "mint": "So111111111111111111111111111111111111111",
  "name": "Example Token",
  "symbol": "EX",
  "description": "An example token",
  "traderPublicKey": "Creator111111111111111111111111111111111111",
  "bondingCurveKey": "BondingCurve111111111111111111111111111111",
  "vTokensInBondingCurve": 793000000000000,
  "vSolInBondingCurve": 30000000000,
  "marketCapSol": 25.5,
  "twitter": "https://twitter.com/example",
  "telegram": "https://t.me/example",
  "website": "https://example.com",
  "imageUri": "https://ipfs.io/ipfs/..."
}
```

**Feld-Beschreibungen:**

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `txType` | string | Immer "create" |
| `mint` | string | Token-Adresse (44 Zeichen) |
| `name` | string | Token-Name |
| `symbol` | string | Token-Symbol (Ticker) |
| `description` | string | Token-Beschreibung |
| `traderPublicKey` | string | Creator-Wallet-Adresse |
| `bondingCurveKey` | string | Bonding-Curve-Adresse |
| `vTokensInBondingCurve` | number | Virtuelle Tokens in Curve |
| `vSolInBondingCurve` | number | Virtuelle SOL in Curve (Lamports) |
| `marketCapSol` | number | Marktkapitalisierung in SOL |
| `twitter` | string | Twitter-URL (optional) |
| `telegram` | string | Telegram-URL (optional) |
| `website` | string | Website-URL (optional) |
| `imageUri` | string | Token-Logo IPFS-URI |

**Verarbeitung im Service:**
```python
# unified_service.py:2401-2403
if data.get("txType") == "create" and "mint" in data:
    await self.process_new_coin(data)
```

---

### buy Event (Kauf)

**Trigger:** Token-Kauf auf pump.fun

**Beispiel-Payload:**
```json
{
  "txType": "buy",
  "mint": "So111111111111111111111111111111111111111",
  "traderPublicKey": "Trader111111111111111111111111111111111111",
  "solAmount": 500000000,
  "tokenAmount": 1500000000000,
  "vSolInBondingCurve": 30500000000,
  "vTokensInBondingCurve": 791500000000000,
  "signature": "4xYz..."
}
```

**Feld-Beschreibungen:**

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `txType` | string | "buy" |
| `mint` | string | Token-Adresse |
| `traderPublicKey` | string | Käufer-Wallet |
| `solAmount` | number | Gekaufte SOL (Lamports) |
| `tokenAmount` | number | Erhaltene Tokens |
| `vSolInBondingCurve` | number | Neue SOL-Reserve |
| `vTokensInBondingCurve` | number | Neue Token-Reserve |
| `signature` | string | Transaktion-Signatur |

**Preis-Berechnung:**
```python
price = vSolInBondingCurve / vTokensInBondingCurve
# Beispiel: 30.5 / 791500 = 0.0000385 SOL pro Token
```

---

### sell Event (Verkauf)

**Trigger:** Token-Verkauf auf pump.fun

**Beispiel-Payload:**
```json
{
  "txType": "sell",
  "mint": "So111111111111111111111111111111111111111",
  "traderPublicKey": "Trader111111111111111111111111111111111111",
  "solAmount": 250000000,
  "tokenAmount": 750000000000,
  "vSolInBondingCurve": 30250000000,
  "vTokensInBondingCurve": 792250000000000,
  "signature": "5aWx..."
}
```

**Verarbeitung im Service:**
```python
# unified_service.py:2405-2419
elif "txType" in data and data["txType"] in ["buy", "sell"]:
    mint = data.get("mint")
    if mint:
        trades_received.inc()

        if mint in self.watchlist:
            # Aktiver Coin - Trade verarbeiten
            self.process_trade(data)
        elif mint in self.coin_cache.cache:
            # Im Cache - Trade sammeln
            self.coin_cache.add_trade(mint, data)
```

---

## Bonding Curve Mathematik

### Preis-Berechnung

```python
price_sol = vSolInBondingCurve / vTokensInBondingCurve
```

**Beispiel:**
- `vSolInBondingCurve`: 30,500,000,000 Lamports (30.5 SOL)
- `vTokensInBondingCurve`: 791,500,000,000,000 Tokens
- Preis: 0.0000000385 SOL pro Token

### Graduation (Raydium Migration)

**Bedingung:** Bonding-Curve zu ~99.5% gefüllt

```python
# Graduation Detection
SOL_RESERVES_FULL = 85.0  # SOL bei voller Bonding Curve

bonding_pct = (vSolInBondingCurve / 1e9) / SOL_RESERVES_FULL * 100
is_graduating = bonding_pct >= 99.5
```

**Was passiert bei Graduation:**
1. Token migriert automatisch zu Raydium
2. Stream wird auf Phase 100 gesetzt
3. `is_graduated = true`
4. Tracking wird beendet

---

## Reconnect-Strategie

### Exponential Backoff

```python
# unified_service.py:2486-2503
reconnect_delay = 1  # Start: 1 Sekunde

while True:
    try:
        async with connect(WS_URI) as ws:
            reconnect_delay = 1  # Reset bei Erfolg
            # ... Normal Operation

    except websockets.exceptions.WebSocketException:
        ws_reconnects.inc()
        unified_status["reconnect_count"] += 1

        print(f"⏳ Reconnect in {reconnect_delay}s...")
        await asyncio.sleep(reconnect_delay)

        # Exponential Backoff (max 60s)
        reconnect_delay = min(reconnect_delay * 2, 60)
```

### Connection-Timeout Detection

```python
# Wenn keine Nachricht seit 300 Sekunden
if now_ts - last_message_time > 300:
    raise websockets.exceptions.ConnectionClosed(1006, "Timeout")
```

---

## Event-Routing-Diagramm

```
WebSocket Message
       │
       ▼
  json.loads(msg)
       │
       ▼
┌──────────────────┐
│ txType == create │──Yes──► process_new_coin()
└────────┬─────────┘         │
         │                   ├─ CoinFilter prüfen
        No                   ├─ In Cache legen
         │                   ├─ Subscribe für Trades
         ▼                   └─ An Discovery-Buffer
┌──────────────────┐
│ txType == buy/   │──Yes──► mint in watchlist?
│          sell    │         │
└────────┬─────────┘        Yes──► process_trade()
         │                   │     │
        No                   │     ├─ OHLCV Update
         │                   │     ├─ Whale Detection
         ▼                   │     └─ ATH Update
    (ignoriert)              │
                            No──► mint in cache?
                                  │
                                 Yes──► cache.add_trade()
                                  │
                                 No──► (ignoriert)
```

---

## Rate Limiting

pumpportal.fun hat implizite Rate Limits:

| Aktion | Empfohlene Rate |
|--------|-----------------|
| Subscription | Max 50 Tokens pro Batch |
| Batch-Intervall | 2 Sekunden |
| Reconnect | Exponential Backoff (1s → 60s) |

**Best Practices:**
1. Subscriptions batchen statt einzeln senden
2. Bei Fehler exponentiell warten
3. Nicht zu viele Tokens gleichzeitig subscriben

---

## Fehlerbehandlung

### ConnectionClosed

```python
except websockets.exceptions.ConnectionClosed as e:
    print(f"🔌 WebSocket Verbindung geschlossen: {e}")
    unified_status["ws_connected"] = False
    ws_connected.set(0)
    # Trigger Reconnect
```

### JSONDecodeError

```python
except json.JSONDecodeError as e:
    print(f"⚠️ JSON Fehler: {e}")
    continue  # Nachricht ignorieren
```

### General Exception

```python
except Exception as e:
    print(f"⚠️ WS Receive Error: {e}")
    unified_status["last_error"] = f"ws_error: {str(e)[:100]}"
    break  # Trigger Reconnect
```

---

## Subscription State Management

### Datenstrukturen

```python
# Bereits abonnierte Tokens
self.subscribed_mints = set()

# Ausstehende Subscriptions
self.pending_subscriptions = set()

# Aktive Watchlist mit Buffer
self.watchlist = {
    "mint123...": {
        "meta": {...},
        "buffer": {...},
        "next_flush": timestamp,
        "interval": 5
    }
}
```

### Subscription-Lifecycle

```
1. Neuer Coin entdeckt
   └─► pending_subscriptions.add(mint)

2. Batch-Task läuft (alle 2s)
   └─► subscribeTokenTrade senden
   └─► subscribed_mints.add(mint)
   └─► pending_subscriptions.remove(mint)

3. Coin aktiviert (>= 3 Trades)
   └─► watchlist[mint] = {...}

4. Coin beendet (Phase 99/100)
   └─► del watchlist[mint]
   └─► subscribed_mints.remove(mint)
```

---

## Weiterführende Dokumentation

- [API-Endpunkte](endpoints.md) - REST API Referenz
- [Coin Discovery](../algorithms/coin-discovery.md) - Filter und Cache
- [Trade Processing](../algorithms/trade-processing.md) - OHLCV-Berechnung

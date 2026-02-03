# Trade Processing Algorithmus

Dokumentation der Trade-Verarbeitung inkl. OHLCV-Berechnung, Whale Detection und ATH-Tracking.

---

## Übersicht

```
Trade Event (buy/sell)
        │
        ▼
┌─────────────────────┐
│  process_trade()    │
│                     │
│  ┌───────────────┐  │
│  │ OHLCV Update  │  │
│  │ Open/High/   │  │
│  │ Low/Close    │  │
│  └───────────────┘  │
│                     │
│  ┌───────────────┐  │
│  │ Volume Stats  │  │
│  │ Buy/Sell/Tot │  │
│  └───────────────┘  │
│                     │
│  ┌───────────────┐  │
│  │ Whale Check   │  │
│  │ >= 1.0 SOL   │  │
│  └───────────────┘  │
│                     │
│  ┌───────────────┐  │
│  │ Dev Tracking  │  │
│  │ Creator Sell │  │
│  └───────────────┘  │
│                     │
│  ┌───────────────┐  │
│  │ ATH Update    │  │
│  │ All-Time-High│  │
│  └───────────────┘  │
│                     │
│  ┌───────────────┐  │
│  │ Buffer Update │  │
│  │ Wallets Set  │  │
│  └───────────────┘  │
└─────────────────────┘
        │
        │ Interval erreicht
        ▼
┌─────────────────────┐
│ check_lifecycle_    │
│ and_flush()         │
│                     │
│  INSERT coin_metrics│
│  Buffer Reset       │
│  Phase Check        │
└─────────────────────┘
```

---

## process_trade() Funktion

**Code-Referenz:** `unified_service.py:1860-1920`

### Vollständiger Code

```python
def process_trade(self, data):
    """Verarbeitet einzelnen Trade"""
    mint = data["mint"]
    if mint not in self.watchlist:
        return

    entry = self.watchlist[mint]
    buf = entry["buffer"]
    now_ts = time.time()

    try:
        sol = float(data["solAmount"])
        price = float(data["vSolInBondingCurve"]) / float(data["vTokensInBondingCurve"])
        is_buy = data["txType"] == "buy"
        trader_key = data.get("traderPublicKey", "")
    except:
        return

    # === ZOMBIE DETECTION: Trade-Timestamp tracken ===
    self.last_trade_timestamps[mint] = now_ts
    self.subscription_watchdog[mint] = now_ts

    print(f"[Trade] {mint[:8]}... @ {price:.2e} SOL - {'BUY' if is_buy else 'SELL'} {sol:.6f} SOL")

    # ATH-Tracking
    known_ath = self.ath_cache.get(mint, 0.0)
    if price > known_ath:
        self.ath_cache[mint] = price
        self.dirty_aths.add(mint)

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
        buf["max_buy"] = max(buf["max_buy"], sol)
        # Whale Check (>= 1.0 SOL)
        if sol >= WHALE_THRESHOLD_SOL:
            buf["whale_buy_vol"] += sol
            buf["whale_buys"] += 1
    else:
        buf["sells"] += 1
        buf["vol_sell"] += sol
        buf["max_sell"] = max(buf["max_sell"], sol)
        # Whale Check
        if sol >= WHALE_THRESHOLD_SOL:
            buf["whale_sell_vol"] += sol
            buf["whale_sells"] += 1
        # Dev-Tracking
        creator_address = entry["meta"].get("creator_address")
        if creator_address and trader_key and trader_key == creator_address:
            buf["dev_sold_amount"] += sol

    # Micro Trade Check (< 0.01 SOL)
    if sol < 0.01:
        buf["micro_trades"] += 1

    # Unique Wallets
    buf["wallets"].add(trader_key)

    # Market Cap Update
    buf["v_sol"] = float(data["vSolInBondingCurve"])
    buf["mcap"] = price * 1_000_000_000  # Total Supply: 1 Billion
```

---

## Buffer-Struktur

**Code-Referenz:** `unified_service.py:1849-1858`

```python
def get_empty_buffer(self):
    """Leerer Buffer für neue Coins"""
    return {
        # OHLCV
        "open": None,              # Erster Preis im Intervall
        "high": -1,                # Höchster Preis
        "low": float("inf"),       # Niedrigster Preis
        "close": 0,                # Letzter Preis

        # Volume
        "vol": 0,                  # Gesamt-Volumen (SOL)
        "vol_buy": 0,              # Kauf-Volumen
        "vol_sell": 0,             # Verkauf-Volumen

        # Trade Counts
        "buys": 0,                 # Anzahl Käufe
        "sells": 0,                # Anzahl Verkäufe

        # Special Stats
        "micro_trades": 0,         # Trades < 0.01 SOL
        "max_buy": 0,              # Größter Einzelkauf
        "max_sell": 0,             # Größter Einzelverkauf

        # Wallets
        "wallets": set(),          # Unique Trader-Adressen

        # Bonding Curve
        "v_sol": 0,                # SOL in Bonding Curve
        "mcap": 0,                 # Market Cap

        # Whale Stats
        "whale_buy_vol": 0,        # Whale-Kauf-Volumen
        "whale_sell_vol": 0,       # Whale-Verkauf-Volumen
        "whale_buys": 0,           # Anzahl Whale-Käufe
        "whale_sells": 0,          # Anzahl Whale-Verkäufe

        # Dev Tracking
        "dev_sold_amount": 0       # Vom Creator verkaufte SOL
    }
```

---

## OHLCV-Berechnung

### Was ist OHLCV?

| Feld | Bedeutung | Beschreibung |
|------|-----------|--------------|
| **O**pen | Eröffnungspreis | Erster Preis im Intervall |
| **H**igh | Höchstpreis | Maximum im Intervall |
| **L**ow | Tiefstpreis | Minimum im Intervall |
| **C**lose | Schlusspreis | Letzter Preis im Intervall |
| **V**olume | Volumen | Gesamtes Handelsvolumen |

### Preis-Berechnung

```python
# Preis = SOL in Curve / Tokens in Curve
price = float(data["vSolInBondingCurve"]) / float(data["vTokensInBondingCurve"])
```

**Beispiel:**
- `vSolInBondingCurve`: 30,500,000,000 Lamports (30.5 SOL)
- `vTokensInBondingCurve`: 791,500,000,000,000 Tokens
- Preis: `30.5 / 791,500,000,000 = 0.0000000385 SOL`

### OHLCV Update-Logik

```python
# Erster Trade im Intervall → Open setzen
if buf["open"] is None:
    buf["open"] = price

# Jeder Trade → Close aktualisieren
buf["close"] = price

# High/Low aktualisieren
buf["high"] = max(buf["high"], price)
buf["low"] = min(buf["low"], price)

# Volumen addieren
buf["vol"] += sol
```

---

## Whale Detection

**Threshold:** `WHALE_THRESHOLD_SOL = 1.0` (1 SOL)

### Definition

Ein "Whale" ist ein Trader, der:
- Mindestens 1.0 SOL in einem einzelnen Trade bewegt
- Potentiell den Preis signifikant beeinflussen kann

### Implementierung

```python
if is_buy:
    if sol >= WHALE_THRESHOLD_SOL:
        buf["whale_buy_vol"] += sol
        buf["whale_buys"] += 1
else:
    if sol >= WHALE_THRESHOLD_SOL:
        buf["whale_sell_vol"] += sol
        buf["whale_sells"] += 1
```

### Gespeicherte Whale-Metriken

| Feld | Beschreibung |
|------|--------------|
| `whale_buys` | Anzahl Käufe >= 1 SOL |
| `whale_sells` | Anzahl Verkäufe >= 1 SOL |
| `whale_buy_volume` | Summe aller Whale-Käufe |
| `whale_sell_volume` | Summe aller Whale-Verkäufe |

---

## Micro Trade Detection

**Threshold:** `< 0.01 SOL`

### Zweck

Micro-Trades können auf:
- Bot-Aktivität hindeuten
- Wash-Trading hinweisen
- Künstliche Volumen-Manipulation sein

### Implementierung

```python
if sol < 0.01:
    buf["micro_trades"] += 1
```

---

## Dev (Creator) Tracking

### Zweck

Verfolgt ob der Token-Ersteller seine eigenen Tokens verkauft ("Dev Dump").

### Implementierung

```python
# Nur bei Verkäufen prüfen
if not is_buy:
    creator_address = entry["meta"].get("creator_address")
    if creator_address and trader_key and trader_key == creator_address:
        buf["dev_sold_amount"] += sol
```

### Bedeutung

| Dev-Sold | Interpretation |
|----------|----------------|
| 0 SOL | Dev hält seine Tokens |
| < 1 SOL | Kleine Entnahme (normal) |
| > 5 SOL | Signifikanter Verkauf (Warnung) |
| > 20 SOL | Potentieller Exit (Alarm) |

---

## ATH (All-Time-High) Tracking

**Code-Referenz:** `unified_service.py:1884-1888`

### In-Memory Cache

```python
# ATH-Cache (mint → höchster Preis)
self.ath_cache = {}

# Geänderte ATHs (für Batch-Update)
self.dirty_aths = set()
```

### Update-Logik

```python
# Bei jedem Trade prüfen
known_ath = self.ath_cache.get(mint, 0.0)
if price > known_ath:
    self.ath_cache[mint] = price
    self.dirty_aths.add(mint)  # Markieren für DB-Update
```

### Batch-Flush

```python
async def flush_ath_updates(self):
    """Schreibt geänderte ATHs in die Datenbank"""
    if not self.dirty_aths:
        return

    for mint in list(self.dirty_aths):
        ath_price = self.ath_cache.get(mint)
        if ath_price:
            await self.pool.execute("""
                UPDATE coin_streams
                SET ath_price_sol = $1
                WHERE token_address = $2
            """, ath_price, mint)

            ath_updates.inc()

    self.dirty_aths.clear()
    self.last_ath_flush = time.time()
```

**Flush-Intervall:** `ATH_FLUSH_INTERVAL = 60` Sekunden

---

## Unique Wallets

### Tracking

```python
# Set für eindeutige Wallet-Adressen
buf["wallets"].add(trader_key)

# Bei Flush: Anzahl ermitteln
unique_wallets = len(buf["wallets"])
```

### Bedeutung

| Wallets | Interpretation |
|---------|----------------|
| 1-5 | Sehr wenige Trader (Bot oder Insider) |
| 5-20 | Normale Early-Coin-Aktivität |
| 20-100 | Gute Verbreitung |
| > 100 | Hohe Adoption |

---

## check_lifecycle_and_flush()

**Code-Referenz:** `unified_service.py:1980-2080`

### Ablauf

```python
async def check_lifecycle_and_flush(self, now_ts=None):
    if now_ts is None:
        now_ts = time.time()

    mints_to_flush = []

    # 1. Finde Coins, deren Intervall erreicht ist
    for mint, entry in self.watchlist.items():
        if now_ts >= entry["next_flush"]:
            mints_to_flush.append(mint)

    if not mints_to_flush:
        return

    # 2. Batch-Insert vorbereiten
    rows = []
    for mint in mints_to_flush:
        entry = self.watchlist[mint]
        buf = entry["buffer"]

        # Keine Trades? Skip (kein leerer Insert)
        if buf["open"] is None:
            entry["next_flush"] = now_ts + entry["interval"]
            continue

        # Metrik-Row erstellen
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

    # 3. Batch-Insert
    if rows:
        await self.pool.executemany("""
            INSERT INTO coin_metrics (
                mint, timestamp,
                price_open, price_high, price_low, price_close,
                volume_sol, volume_buy_sol, volume_sell_sol,
                num_buys, num_sells, unique_wallets,
                whale_buys, whale_sells,
                whale_buy_volume, whale_sell_volume,
                dev_sold_sol, micro_trades, market_cap_sol
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
        """, rows)

        metric_batches_saved.inc()
        metrics_saved.inc(len(rows))
        unified_status["total_metrics_saved"] += len(rows)
```

---

## Graduation Detection

**Code-Referenz:** `unified_service.py:2063-2085`

### Bedingung

```python
SOL_RESERVES_FULL = 85.0  # SOL bei voller Bonding Curve

bonding_pct = (buf["v_sol"] / 1e9) / SOL_RESERVES_FULL * 100
is_graduating = bonding_pct >= 99.5
```

### Verarbeitung

```python
if is_graduating:
    await self.stop_tracking(mint, is_graduation=True)
    # → Phase 100, is_graduated = true

async def stop_tracking(self, mint, is_graduation=False):
    if is_graduation:
        print(f"🎉 GRADUATION: {mint[:8]}... geht zu Raydium!")
        final_phase = 100
        graduated_flag = True
        coins_graduated.inc()
    else:
        print(f"🏁 FINISHED: {mint[:8]}... Lifecycle beendet")
        final_phase = 99
        graduated_flag = False
        coins_finished.inc()

    await self.pool.execute("""
        UPDATE coin_streams
        SET is_active = FALSE, current_phase_id = $2, is_graduated = $3
        WHERE token_address = $1
    """, mint, final_phase, graduated_flag)
```

---

## Prometheus Metriken

| Metrik | Typ | Beschreibung |
|--------|-----|--------------|
| `unified_trades_received_total` | Counter | Alle empfangenen Trades |
| `unified_trades_processed_total` | Counter | Verarbeitete Trades |
| `unified_metrics_saved_total` | Counter | Gespeicherte Metrik-Einträge |
| `unified_metric_batches_saved_total` | Counter | Batch-Inserts |
| `unified_ath_updates_total` | Counter | ATH-Updates |
| `unified_coins_graduated_total` | Counter | Graduierte Coins |
| `unified_coins_finished_total` | Counter | Beendete Coins |

---

## Konfigurationsparameter

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `WHALE_THRESHOLD_SOL` | 1.0 | Whale-Grenze in SOL |
| `SOL_RESERVES_FULL` | 85.0 | SOL bei voller Curve |
| `ATH_FLUSH_INTERVAL` | 60 | ATH-Flush alle X Sekunden |
| `TRADE_BUFFER_SECONDS` | 5 | Min. Zeit zwischen Flushes |

---

## Weiterführende Dokumentation

- [Phase Management](phase-management.md) - Lifecycle-Phasen
- [Coin Discovery](coin-discovery.md) - Wie Coins entdeckt werden
- [Datenbank Schema](../database/schema.md) - coin_metrics Tabelle

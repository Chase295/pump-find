# Zombie Detection Algorithmus

Dokumentation des Stale-Stream-Detection und Force-Resubscribe Mechanismus.

---

## Problem

WebSocket-Subscriptions können "stillschweigend" fehlschlagen:
- Server vergisst Subscription
- Netzwerk-Probleme unterbrechen Verbindung
- Coin hat tatsächlich keine Trades mehr

**Symptome:**
- Coin ist in Watchlist aktiv
- Keine neuen Trades kommen an
- Buffer bleibt leer oder stagniert

---

## Lösung: Zombie Detection

Das System erkennt "Zombie-Streams" und versucht sie zu reaktivieren.

```
┌─────────────────────────────────────────────────────────┐
│                   Zombie Detection                       │
│                                                          │
│  ┌─────────────┐     ┌─────────────┐     ┌────────────┐ │
│  │ Trade kommt │────►│ Timestamp   │     │ Watchdog   │ │
│  │             │     │ aktualisiert│     │ (60s)      │ │
│  └─────────────┘     └─────────────┘     └─────┬──────┘ │
│                                                │        │
│                              ┌─────────────────┘        │
│                              ▼                          │
│                      ┌───────────────┐                  │
│                      │ Inaktiv seit  │                  │
│                      │ > 10 Minuten? │                  │
│                      └───────┬───────┘                  │
│                              │                          │
│                    ┌─────────┴─────────┐                │
│                    │                   │                │
│                   Nein                Ja                │
│                    │                   │                │
│                    ▼                   ▼                │
│              ┌──────────┐      ┌──────────────┐        │
│              │  OK      │      │ Force        │        │
│              │  Weiter  │      │ Re-Subscribe │        │
│              └──────────┘      └──────────────┘        │
│                                        │                │
│                                        ▼                │
│                                ┌──────────────┐        │
│                                │ unsubscribe  │        │
│                                │ + subscribe  │        │
│                                └──────────────┘        │
└─────────────────────────────────────────────────────────┘
```

---

## Implementierung

### Trade-Timestamp Tracking

**Code-Referenz:** `unified_service.py:1878-1880`

```python
def process_trade(self, data):
    mint = data["mint"]
    now_ts = time.time()

    # Timestamp bei jedem Trade aktualisieren
    self.last_trade_timestamps[mint] = now_ts
    self.subscription_watchdog[mint] = now_ts
```

### Subscription Watchdog

**Code-Referenz:** `unified_service.py:1921-1937`

```python
async def check_subscription_watchdog(self, now_ts):
    """Watchdog: Prüfe alle aktiven Coins auf zu lange Inaktivität"""
    inactive_coins = []

    for mint, entry in self.watchlist.items():
        last_trade = self.last_trade_timestamps.get(mint, 0)
        time_since_trade = now_ts - last_trade

        # 10 Minuten ohne Trades = kritisch
        if time_since_trade > 600:
            inactive_coins.append((mint, time_since_trade))

    if inactive_coins:
        print(f"[Watchdog] 🚨 {len(inactive_coins)} Coins ohne Trades seit >10 Min!")
        for mint, inactive_time in inactive_coins:
            print(f"[Watchdog]   {mint[:8]}... - {inactive_time:.0f}s ohne Trades")
            await self.force_resubscribe(mint)
```

### Watchdog-Aufruf

```python
# Im Main-Loop (alle 60 Sekunden)
if int(now_ts) % 60 == 0:
    await self.check_subscription_watchdog(now_ts)
```

---

## Force Re-Subscribe

**Code-Referenz:** `unified_service.py:1939-1966`

```python
async def force_resubscribe(self, mint):
    """Force re-subscribe für einen Coin um WebSocket-Verbindung zu erneuern"""
    if mint not in self.watchlist:
        return

    try:
        if hasattr(self, 'websocket') and self.websocket:
            print(f"[WebSocket] Force Re-Subscribe für {mint[:8]}...")

            # 1. Unsubscribe
            unsubscribe_msg = {"method": "unsubscribeTokenTrade", "keys": [mint]}
            await self.websocket.send(json.dumps(unsubscribe_msg))
            await asyncio.sleep(0.1)  # Kurze Pause

            # 2. Subscribe
            subscribe_msg = {"method": "subscribeTokenTrade", "keys": [mint]}
            await self.websocket.send(json.dumps(subscribe_msg))

            # 3. Watchdog-Timer zurücksetzen
            self.subscription_watchdog[mint] = time.time()

            print(f"[WebSocket] ✓ Re-Subscription gesendet für {mint[:8]}...")
        else:
            print(f"[WebSocket] ❌ Keine aktive WebSocket-Verbindung")

    except Exception as e:
        print(f"[WebSocket] ❌ Fehler bei Re-Subscribe: {e}")
```

---

## Stale Data Detection

**Code-Referenz:** `unified_service.py:2139-2150`

### Problem

Ein Coin kann Trades haben, aber die Daten ändern sich nicht mehr (z.B. identische Preise).

### Lösung: Signature-basierte Erkennung

```python
# Bei Metric-Flush
if now_ts >= entry["next_flush"]:
    # Watchdog-Check: Wann kam der letzte Trade?
    last_trade = self.last_trade_timestamps.get(mint, 0)
    time_since_last_trade = now_ts - last_trade
    is_stale = time_since_last_trade > 300  # 5 Minuten ohne Trades

    # Stale Data Detection: Speichere nur wenn sich Daten geändert haben
    should_save = False
    if buf["vol"] > 0:
        # Signatur aus Buffer-Daten erstellen
        current_signature = (buf["vol"], buf["close"], len(buf["wallets"]))
        last_saved_signature = self.last_saved_signatures.get(mint)

        if current_signature != last_saved_signature:
            should_save = True
            self.last_saved_signatures[mint] = current_signature
```

---

## Phase-Transition Re-Subscribe

**Code-Referenz:** `unified_service.py:2134-2137`

Nach einem Phase-Wechsel wird automatisch re-subscribed:

```python
# Nach Phase-Wechsel
await self.switch_phase(mint, current_pid, next_pid)
entry["meta"]["phase_id"] = next_pid
entry["interval"] = self.phases_config[next_pid]["interval"]

# Force re-subscribe um Subscription zu garantieren
print(f"[WebSocket] {mint[:8]}... - Phase-Wechsel: Subscription-Check")
await self.force_resubscribe(mint)
```

**Warum?**
- Phase-Wechsel können Timing-Probleme verursachen
- Sicherstellung dass WebSocket-Events weiterhin ankommen

---

## Datenstrukturen

```python
# Letzte Trade-Timestamps pro Coin
self.last_trade_timestamps = {}  # mint → timestamp

# Subscription-Watchdog Timer
self.subscription_watchdog = {}  # mint → timestamp

# Letzte gespeicherte Signaturen (für Stale Detection)
self.last_saved_signatures = {}  # mint → (vol, close, wallets)
```

---

## Timing-Parameter

| Parameter | Wert | Beschreibung |
|-----------|------|--------------|
| Watchdog-Intervall | 60s | Alle 60 Sekunden prüfen |
| Inaktivitäts-Threshold | 600s | 10 Minuten ohne Trades |
| Stale-Threshold | 300s | 5 Minuten für Stale-Detection |
| Re-Subscribe Pause | 0.1s | Pause zwischen unsub/sub |

---

## Log-Ausgaben

```
# Normal Operation
[Trade] So11111... @ 3.85e-08 SOL - BUY 0.500000 SOL

# Watchdog-Warnung
[Watchdog] 🚨 3 Coins ohne Trades seit >10 Min!
[Watchdog]   So11111... - 650s ohne Trades
[Watchdog]   Abc2222... - 720s ohne Trades
[Watchdog]   Xyz3333... - 890s ohne Trades

# Force Re-Subscribe
[WebSocket] Force Re-Subscribe für So11111...
[WebSocket] ✓ Re-Subscription gesendet für So11111...

# Phase-Transition
[WebSocket] So11111... - Phase-Wechsel: Subscription-Check
[WebSocket] Force Re-Subscribe für So11111...
```

---

## Failure Modes

### 1. Echter Dead Coin

**Symptom:** Coin hat tatsächlich keine Aktivität mehr

**Verhalten:**
- Re-Subscribe hilft nicht
- Coin wird bei max_age zu Phase 99

### 2. Server-seitiges Problem

**Symptom:** pumpportal.fun hat Subscription "vergessen"

**Verhalten:**
- Re-Subscribe stellt Events wieder her
- Trades kommen wieder an

### 3. Netzwerk-Problem

**Symptom:** WebSocket-Verbindung instabil

**Verhalten:**
- Re-Subscribe schlägt evtl. fehl
- Reconnect-Mechanismus greift

---

## Prometheus Metriken

| Metrik | Typ | Beschreibung |
|--------|-----|--------------|
| `unified_zombie_coins_detected` | Counter | Erkannte Zombie-Coins |
| `unified_force_resubscribes_total` | Counter | Force Re-Subscribes |
| `unified_stale_data_skipped` | Counter | Übersprungene Stale-Saves |

---

## Manueller Cleanup

```sql
-- Zombie-Coins in der Datenbank finden
SELECT token_address, started_at, current_phase_id
FROM coin_streams
WHERE is_active = true
  AND started_at < NOW() - INTERVAL '2 hours'
  AND NOT EXISTS (
    SELECT 1 FROM coin_metrics cm
    WHERE cm.mint = token_address
    AND cm.timestamp > NOW() - INTERVAL '30 minutes'
  );

-- Manueller Cleanup (Vorsicht!)
UPDATE coin_streams
SET is_active = false, current_phase_id = 99
WHERE is_active = true
  AND started_at < NOW() - INTERVAL '4 hours'
  AND NOT EXISTS (...);
```

---

## Weiterführende Dokumentation

- [WebSocket-Protokoll](../api/websocket.md) - Subscribe/Unsubscribe
- [Phase Management](phase-management.md) - Lifecycle-Ende
- [Trade Processing](trade-processing.md) - Timestamp-Tracking

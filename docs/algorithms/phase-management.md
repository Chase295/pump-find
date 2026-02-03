# Phase Management Algorithmus

Dokumentation des Lifecycle-Systems für Token-Tracking.

---

## Übersicht

```
Coin Aktiviert (>= 3 Trades)
         │
         ▼
    ┌─────────┐
    │ Phase 1 │ Baby Zone (0-10 min)
    │  5s     │ Interval: 5 Sekunden
    └────┬────┘
         │ age > 10 min
         ▼
    ┌─────────┐
    │ Phase 2 │ Survival Zone (10-120 min)
    │  15s    │ Interval: 15 Sekunden
    └────┬────┘
         │ age > 120 min
         ▼
    ┌─────────┐
    │ Phase 3 │ Mature Zone (120-240 min)
    │  15s    │ Interval: 15 Sekunden
    └────┬────┘
         │ age > 240 min
         ▼
    ┌─────────┐
    │Phase 99 │ Finished (Timeout)
    │ inactive│ is_active = false
    └─────────┘

ODER bei Graduation (bonding_pct >= 99.5%):

    ┌──────────┐
    │ Phase 100│ Graduated (Raydium)
    │  inactive│ is_graduated = true
    └──────────┘
```

---

## Default-Phasen

| ID | Name | Interval | Min Age | Max Age | Bedeutung |
|----|------|----------|---------|---------|-----------|
| 1 | Baby Zone | 5s | 0 min | 10 min | Hochfrequentes Tracking |
| 2 | Survival Zone | 15s | 10 min | 120 min | Mittleres Tracking |
| 3 | Mature Zone | 15s | 120 min | 240 min | Etablierte Coins |
| 99 | Finished | - | - | - | Timeout (System) |
| 100 | Graduated | - | - | - | Raydium Migration (System) |

### Phase-Logik

- **Phase 1 (Baby):** Erste 10 Minuten, maximale Datenerfassung alle 5s
- **Phase 2 (Survival):** 10-120 Minuten, reduziertes Tracking alle 15s
- **Phase 3 (Mature):** 2-4 Stunden, langfristiges Tracking alle 15s
- **Phase 99 (Finished):** Coin hat max_age überschritten, Tracking beendet
- **Phase 100 (Graduated):** Coin ist zu Raydium migriert

---

## Phasen-Konfiguration

**Datenbank-Tabelle:** `ref_coin_phases`

```sql
CREATE TABLE ref_coin_phases (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    interval_seconds INTEGER NOT NULL,
    min_age_minutes INTEGER NOT NULL,
    max_age_minutes INTEGER NOT NULL
);
```

### In-Memory Cache

```python
# unified_service.py
self.phases_config = {
    1: {
        "id": 1,
        "name": "Baby Zone",
        "interval": 5,
        "min_age": 0,
        "max_age": 10
    },
    2: {...},
    ...
}

# Sortierte IDs für Phase-Lookup
self.sorted_phase_ids = [1, 2, 3, 99, 100]
```

---

## Phase-Upgrade Algorithmus

**Code-Referenz:** `unified_service.py:2108-2137`

```python
async def check_lifecycle_and_flush(self, now_ts):
    for mint, entry in list(self.watchlist.items()):
        # Coin-Alter berechnen
        created_at = entry["meta"]["created_at"]
        current_pid = entry["meta"]["phase_id"]
        diff = now_utc - created_at
        age_minutes = (diff.total_seconds() / 60) - AGE_CALCULATION_OFFSET_MIN

        # Phase-Konfiguration laden
        phase_cfg = self.phases_config.get(current_pid)

        # Prüfen ob max_age überschritten
        if phase_cfg and age_minutes > phase_cfg["max_age"]:
            # Nächste Phase finden
            next_pid = None
            for pid in self.sorted_phase_ids:
                if pid > current_pid:
                    next_pid = pid
                    break

            # Keine weitere Phase oder System-Phase?
            if next_pid is None or next_pid >= 99:
                await self.stop_tracking(mint, is_graduation=False)
            else:
                # Phase wechseln
                await self.switch_phase(mint, current_pid, next_pid)
                entry["meta"]["phase_id"] = next_pid
                entry["interval"] = self.phases_config[next_pid]["interval"]
                entry["next_flush"] = now_ts + new_interval

                # Force Re-Subscribe nach Phase-Wechsel
                await self.force_resubscribe(mint)
```

### switch_phase()

```python
async def switch_phase(self, mint, old_phase, new_phase):
    """Phase wechseln"""
    print(f"🆙 Phase {old_phase} -> {new_phase} für {mint[:8]}...")
    await self.pool.execute(
        "UPDATE coin_streams SET current_phase_id = $1 WHERE token_address = $2",
        new_phase, mint
    )
    phase_switches.inc()
```

---

## Graduation Detection

**Code-Referenz:** `unified_service.py:2101-2106`

### Bedingung

```python
SOL_RESERVES_FULL = 85.0  # SOL bei voller Bonding Curve

current_bonding_pct = (buf["v_sol"] / SOL_RESERVES_FULL) * 100

if current_bonding_pct >= 99.5:
    await self.stop_tracking(mint, is_graduation=True)
```

### Was passiert bei Graduation?

1. Bonding Curve ist zu 99.5%+ gefüllt
2. Token migriert automatisch zu Raydium
3. Stream wird auf Phase 100 gesetzt
4. `is_graduated = true`
5. `is_active = false`
6. Tracking wird beendet

---

## stop_tracking()

**Code-Referenz:** `unified_service.py:2063-2090`

```python
async def stop_tracking(self, mint, is_graduation=False):
    """Tracking beenden"""
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

    # Datenbank-Update
    await self.pool.execute("""
        UPDATE coin_streams
        SET is_active = FALSE,
            current_phase_id = $2,
            is_graduated = $3
        WHERE token_address = $1
    """, mint, final_phase, graduated_flag)

    # Cleanup
    if mint in self.watchlist:
        del self.watchlist[mint]
    if mint in self.subscribed_mints:
        self.subscribed_mints.remove(mint)
    if mint in self.dirty_aths:
        self.dirty_aths.remove(mint)

    coins_tracked.set(len(self.watchlist))
```

---

## CRUD API

### GET /database/phases

```bash
curl http://localhost:3001/api/database/phases
```

**Response:**
```json
{
  "phases": [
    {"id": 1, "name": "Baby Zone", "interval_seconds": 5, "min_age_minutes": 0, "max_age_minutes": 10},
    {"id": 2, "name": "Survival Zone", "interval_seconds": 15, "min_age_minutes": 10, "max_age_minutes": 120},
    ...
  ],
  "count": 5
}
```

### POST /database/phases (Create)

```bash
curl -X POST http://localhost:3001/api/database/phases \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Extended Zone",
    "interval_seconds": 30,
    "min_age_minutes": 240,
    "max_age_minutes": 480
  }'
```

**Validierung:**
- `interval_seconds >= 1`
- `max_age_minutes > min_age_minutes`
- `min_age_minutes >= 0`
- ID automatisch vergeben (1-98)

### PUT /database/phases/{id} (Update)

```bash
curl -X PUT http://localhost:3001/api/database/phases/1 \
  -H "Content-Type: application/json" \
  -d '{"interval_seconds": 10}'
```

**Live-Reload:**
Nach Update werden alle aktiven Streams mit neuen Intervallen aktualisiert.

```python
async def reload_phases_config(self):
    """Lädt Phasen neu und aktualisiert aktive Streams"""
    # 1. Aus DB laden
    rows = await self.pool.fetch("SELECT * FROM ref_coin_phases")
    self.phases_config = {r["id"]: {...} for r in rows}

    # 2. Watchlist aktualisieren
    updated = 0
    for mint, entry in self.watchlist.items():
        phase_id = entry["phase_id"]
        if phase_id in self.phases_config:
            entry["interval"] = self.phases_config[phase_id]["interval_seconds"]
            updated += 1

    return updated
```

### DELETE /database/phases/{id} (Delete)

```bash
curl -X DELETE http://localhost:3001/api/database/phases/4
```

**Stream-Migration:**
Betroffene Streams werden zur nächsten Phase verschoben.

```python
# Nächste Phase finden
next_phase = await pool.fetchrow("""
    SELECT id FROM ref_coin_phases
    WHERE id > $1 AND id < 99
    ORDER BY id ASC LIMIT 1
""", phase_id)

target = next_phase['id'] if next_phase else 99

# Streams verschieben
await pool.execute("""
    UPDATE coin_streams
    SET current_phase_id = $1
    WHERE current_phase_id = $2 AND is_active = true
""", target, phase_id)
```

---

## System-Phasen (99, 100)

### Schutz

System-Phasen können NICHT:
- Bearbeitet werden
- Gelöscht werden

```python
# PUT /database/phases/{id}
if phase_id >= 99:
    raise HTTPException(
        status_code=400,
        detail="System-Phasen (99, 100) können nicht bearbeitet werden"
    )
```

### Verwendung

| Phase | Bedeutung | Trigger |
|-------|-----------|---------|
| 99 | Finished | Coin erreicht max_age der letzten Phase |
| 100 | Graduated | bonding_pct >= 99.5% |

---

## Watchlist-Eintrag Struktur

```python
self.watchlist[mint] = {
    "meta": {
        "token_address": mint,
        "name": "Example Token",
        "symbol": "EX",
        "creator_address": "...",
        "created_at": datetime(...),
        "phase_id": 1,
        ...
    },
    "buffer": {
        "open": None,
        "high": -1,
        "low": float("inf"),
        ...
    },
    "next_flush": time.time() + 5,  # Nächster Flush-Zeitpunkt
    "interval": 5                     # Aktuelles Intervall
}
```

---

## Age Calculation Offset

```python
AGE_CALCULATION_OFFSET_MIN = 2  # 2 Minuten Offset

age_minutes = (diff.total_seconds() / 60) - AGE_CALCULATION_OFFSET_MIN
```

**Zweck:** Berücksichtigt Verzögerung zwischen Token-Erstellung und Aktivierung.

---

## Prometheus Metriken

| Metrik | Typ | Beschreibung |
|--------|-----|--------------|
| `unified_phase_switches_total` | Counter | Anzahl Phase-Wechsel |
| `unified_coins_finished_total` | Counter | Beendete Coins (Timeout) |
| `unified_coins_graduated_total` | Counter | Graduierte Coins |
| `unified_coins_tracked` | Gauge | Aktuell getrackte Coins |

---

## Beispiel-Lifecycle

```
t=0:     Coin erstellt auf pump.fun
t=1:     Trade #1 → Cache
t=3:     Trade #2 → Cache
t=5:     Trade #3 → Aktivierung!
         → Phase 1 (Baby Zone, 5s Interval)
         → INSERT discovered_coins
         → INSERT coin_streams (phase_id=1)

t=600:   age=10 min > max_age(Phase 1)=10 min
         → Phase 2 (Survival Zone, 15s Interval)
         → UPDATE coin_streams SET current_phase_id=2

t=7200:  age=120 min > max_age(Phase 2)=120 min
         → Phase 3 (Mature Zone, 15s Interval)

t=14400: age=240 min > max_age(Phase 3)=240 min
         → Phase 99 (Finished)
         → is_active = false
         → Tracking beendet

ODER:

t=3000:  bonding_pct=99.7%
         → Phase 100 (Graduated)
         → is_graduated = true
         → is_active = false
         → Tracking beendet
```

---

## Weiterführende Dokumentation

- [API-Endpunkte](../api/endpoints.md) - Phase CRUD API
- [Trade Processing](trade-processing.md) - Buffer und Flush
- [Zombie Detection](zombie-detection.md) - Stale Stream Handling

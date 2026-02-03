# API-Endpunkte Referenz

Vollständige Dokumentation aller REST API Endpunkte des Pump Finder Services.

---

## Übersicht

| Kategorie | Endpunkt | Methode | Beschreibung |
|-----------|----------|---------|--------------|
| **Health & Metrics** | `/health` | GET | Service-Status und Statistiken |
| | `/metrics` | GET | Prometheus Metriken |
| **Konfiguration** | `/config` | GET | Aktuelle Konfiguration |
| | `/config` | PUT | Konfiguration aktualisieren |
| | `/reload-config` | POST | Konfiguration neu laden |
| **Phase Management** | `/database/phases` | GET | Alle Phasen auflisten |
| | `/database/phases` | POST | Neue Phase erstellen |
| | `/database/phases/{id}` | PUT | Phase aktualisieren |
| | `/database/phases/{id}` | DELETE | Phase löschen |
| **Database** | `/database/streams` | GET | Coin-Streams auflisten |
| | `/database/streams/stats` | GET | Stream-Statistiken |
| | `/database/metrics` | GET | Historische Metriken |
| **Analytics** | `/analytics/{mint}` | GET | Coin-Performance-Analyse |

---

## Health & Metrics

### GET /health

**Zweck:** Service-Gesundheitsstatus mit detaillierten Statistiken

**Code-Referenz:** `unified_service.py:659-775`

**Response:**
```json
{
  "status": "healthy",           // healthy | degraded | unhealthy
  "ws_connected": true,          // WebSocket zu pumpportal.fun
  "db_connected": true,          // PostgreSQL Verbindung
  "uptime_seconds": 3600,        // Service-Laufzeit
  "last_message_ago": 5,         // Sekunden seit letzter WS-Nachricht
  "reconnect_count": 0,          // WebSocket Reconnect-Zähler
  "last_error": null,            // Letzter Fehler (oder null)
  "cache_stats": {
    "total_coins": 45,           // Coins im 120s Cache
    "activated_coins": 12,       // Davon aktiviert
    "expired_coins": 33,         // Davon abgelaufen
    "oldest_age_seconds": 119,
    "newest_age_seconds": 3
  },
  "tracking_stats": {
    "active_coins": 229,         // Coins mit aktivem Stream
    "total_trades": 15420,       // Alle verarbeiteten Trades
    "total_metrics_saved": 8750  // Gespeicherte Metrik-Einträge
  },
  "discovery_stats": {
    "total_coins_discovered": 1523,  // Alle entdeckten Coins
    "n8n_available": true,           // n8n Webhook erreichbar
    "n8n_buffer_size": 3             // Coins im Buffer für n8n
  }
}
```

**Status-Logik:**
```python
# healthy: Beide Verbindungen OK
status = "healthy" if (db_status and ws_status) else "degraded"

# WebSocket gilt als verbunden wenn letzte Nachricht < 5min alt
ws_status = (time.time() - last_message_time) < 300
```

**Beispiel-Request:**
```bash
curl -s http://localhost:3001/api/health | jq
```

---

### GET /metrics

**Zweck:** Prometheus-kompatible Metriken für Monitoring

**Code-Referenz:** `unified_service.py:789-808`

**Response:** Plain Text (Prometheus Format)

```prometheus
# HELP pump_coins_received_total Total coins received from WebSocket
# TYPE pump_coins_received_total counter
pump_coins_received_total 1523.0

# HELP pump_cache_size Current number of coins in cache
# TYPE pump_cache_size gauge
pump_cache_size 45.0

# HELP pump_active_streams Number of active coin streams
# TYPE pump_active_streams gauge
pump_active_streams 229.0

# HELP pump_uptime_seconds Service uptime in seconds
# TYPE pump_uptime_seconds gauge
pump_uptime_seconds 3600.0

# ... 50+ weitere Metriken
```

**Wichtige Metriken-Kategorien:**

| Kategorie | Präfix | Beispiel |
|-----------|--------|----------|
| Discovery | `pump_coins_` | `pump_coins_received_total` |
| Cache | `pump_cache_` | `pump_cache_activations_total` |
| Tracking | `pump_metric_` | `pump_metric_trades_processed` |
| n8n | `pump_n8n_` | `pump_n8n_batch_sent_total` |
| ATH | `pump_ath_` | `pump_ath_updates_total` |

**Beispiel-Request:**
```bash
curl http://localhost:3001/api/metrics
```

---

## Konfiguration

### GET /config

**Zweck:** Aktuelle Service-Konfiguration abrufen

**Code-Referenz:** `unified_service.py:1035-1067`

**Response:**
```json
{
  "n8n_webhook_url": "https://n8n.example.com/webhook/pump",
  "n8n_webhook_method": "POST",
  "db_dsn": "postgresql://user:***@host:5432/pump",  // Passwort maskiert
  "coin_cache_seconds": 120,
  "db_refresh_interval": 60,
  "batch_size": 10,
  "batch_timeout": 30,
  "bad_names_pattern": "test|bot|rug|scam|cant|honey|faucet",
  "spam_burst_window": 30,
  "sol_reserves_full": 85.0,
  "whale_threshold_sol": 1.0,
  "age_calculation_offset_min": 2,
  "trade_buffer_seconds": 5,
  "ath_flush_interval": 60
}
```

**Sicherheit:**
- `db_dsn` zeigt immer `***` anstelle des Passworts
- Sensible Daten werden nie im Klartext zurückgegeben

---

### PUT /config

**Zweck:** Konfiguration zur Laufzeit ändern (persistiert in `.env`)

**Code-Referenz:** `unified_service.py:902-1033`

**Request Body (alle Felder optional):**
```json
{
  "n8n_webhook_url": "https://new-n8n.example.com/webhook",
  "n8n_webhook_method": "POST",
  "coin_cache_seconds": 180,
  "batch_size": 15,
  "batch_timeout": 45,
  "bad_names_pattern": "test|bot|rug|scam",
  "spam_burst_window": 20
}
```

**Request Model (Pydantic):**
```python
class ConfigUpdateRequest(BaseModel):
    n8n_webhook_url: Optional[str] = None
    n8n_webhook_method: Optional[str] = None
    db_dsn: Optional[str] = None
    coin_cache_seconds: Optional[int] = None
    db_refresh_interval: Optional[int] = None
    batch_size: Optional[int] = None
    batch_timeout: Optional[int] = None
    bad_names_pattern: Optional[str] = None
    spam_burst_window: Optional[int] = None
```

**Response:**
```json
{
  "status": "success",
  "message": "Konfiguration aktualisiert",
  "updated_fields": ["batch_size", "batch_timeout"],
  "new_config": {
    "batch_size": 15,
    "batch_timeout": 45,
    // ... alle Felder
  }
}
```

**Verhalten:**
1. Nur geänderte Felder werden aktualisiert
2. Änderungen werden sofort wirksam (globale Variablen)
3. Änderungen werden in `.env` persistiert
4. Bei Regex-Pattern (`bad_names_pattern`) wird das Pattern neu kompiliert

**Beispiel-Request:**
```bash
curl -X PUT http://localhost:3001/api/config \
  -H "Content-Type: application/json" \
  -d '{"batch_size": 15, "batch_timeout": 45}'
```

---

### POST /reload-config

**Zweck:** Konfiguration aus `.env`-Datei neu laden

**Code-Referenz:** `unified_service.py:810-832`

**Response:**
```json
{
  "status": "success",
  "message": "Konfiguration wurde neu geladen",
  "config": {
    "COIN_CACHE_SECONDS": 120,
    "DB_REFRESH_INTERVAL": 60,
    "BATCH_SIZE": 10
  }
}
```

**Verhalten:**
- Lädt `.env`-Datei neu
- Aktualisiert globale Variablen
- Lädt Phasen-Konfiguration aus Datenbank neu

---

## Phase Management

### GET /database/phases

**Zweck:** Alle Tracking-Phasen auflisten

**Code-Referenz:** `unified_service.py:1070-1085`

**Response:**
```json
{
  "phases": [
    {
      "id": 1,
      "name": "Baby Zone",
      "interval_seconds": 5,
      "min_age_minutes": 0,
      "max_age_minutes": 10
    },
    {
      "id": 2,
      "name": "Survival Zone",
      "interval_seconds": 15,
      "min_age_minutes": 10,
      "max_age_minutes": 120
    },
    {
      "id": 3,
      "name": "Mature Zone",
      "interval_seconds": 15,
      "min_age_minutes": 120,
      "max_age_minutes": 240
    },
    {
      "id": 99,
      "name": "Finished",
      "interval_seconds": 0,
      "min_age_minutes": 0,
      "max_age_minutes": 0
    },
    {
      "id": 100,
      "name": "Graduated",
      "interval_seconds": 0,
      "min_age_minutes": 0,
      "max_age_minutes": 0
    }
  ],
  "count": 5
}
```

**Phase-System:**

| ID | Bedeutung | Editierbar |
|----|-----------|------------|
| 1-98 | Reguläre Phasen | Ja |
| 99 | Finished (Timeout) | Nein |
| 100 | Graduated (Bonding Complete) | Nein |

---

### POST /database/phases

**Zweck:** Neue Tracking-Phase erstellen

**Code-Referenz:** `unified_service.py:1151-1210`

**Request Body:**
```json
{
  "name": "Extended Zone",
  "interval_seconds": 30,
  "min_age_minutes": 240,
  "max_age_minutes": 480
}
```

**Request Model:**
```python
class PhaseCreateRequest(BaseModel):
    name: str
    interval_seconds: int      # >= 1
    min_age_minutes: int       # >= 0
    max_age_minutes: int       # > min_age_minutes
```

**Response:**
```json
{
  "status": "success",
  "message": "Phase 4 'Extended Zone' erfolgreich erstellt",
  "phase": {
    "id": 4,
    "name": "Extended Zone",
    "interval_seconds": 30,
    "min_age_minutes": 240,
    "max_age_minutes": 480
  }
}
```

**Validierung:**
- `interval_seconds >= 1`
- `max_age_minutes > min_age_minutes`
- `min_age_minutes >= 0`
- Maximal 98 reguläre Phasen (ID 1-98)

**ID-Vergabe:**
```python
# Nächste freie ID zwischen 1 und 98
for i in range(1, 99):
    if i not in used_ids:
        new_id = i
        break
```

**Beispiel-Request:**
```bash
curl -X POST http://localhost:3001/api/database/phases \
  -H "Content-Type: application/json" \
  -d '{"name": "Extended Zone", "interval_seconds": 30, "min_age_minutes": 240, "max_age_minutes": 480}'
```

---

### PUT /database/phases/{phase_id}

**Zweck:** Existierende Phase aktualisieren

**Code-Referenz:** `unified_service.py:1088-1148`

**URL-Parameter:**
- `phase_id` (int): Phase-ID (1-98, System-Phasen 99/100 nicht editierbar)

**Request Body (alle Felder optional):**
```json
{
  "name": "Updated Name",
  "interval_seconds": 10,
  "min_age_minutes": 0,
  "max_age_minutes": 15
}
```

**Request Model:**
```python
class PhaseUpdateRequest(BaseModel):
    name: Optional[str] = None
    interval_seconds: Optional[int] = None
    min_age_minutes: Optional[int] = None
    max_age_minutes: Optional[int] = None
```

**Response:**
```json
{
  "status": "success",
  "message": "Phase 1 erfolgreich aktualisiert",
  "phase": {
    "id": 1,
    "name": "Updated Name",
    "interval_seconds": 10,
    "min_age_minutes": 0,
    "max_age_minutes": 15
  },
  "updated_streams": 45
}
```

**Live-Reload-Mechanismus:**
```python
# Nach Update wird reload_phases_config() aufgerufen
# Alle aktiven Streams werden mit neuen Intervallen aktualisiert

async def reload_phases_config(self):
    # 1. Phasen aus DB laden
    rows = await self.pool.fetch("SELECT * FROM ref_coin_phases")
    self.phases_config = {r["id"]: dict(r) for r in rows}

    # 2. Watchlist-Einträge aktualisieren
    updated = 0
    for mint, entry in self.watchlist.items():
        phase_id = entry["phase_id"]
        if phase_id in self.phases_config:
            new_interval = self.phases_config[phase_id]["interval_seconds"]
            entry["interval"] = new_interval
            updated += 1

    return updated
```

**Fehler:**
- `400`: System-Phase (99/100) kann nicht bearbeitet werden
- `400`: Validierungsfehler (interval < 1, max <= min)
- `404`: Phase nicht gefunden

---

### DELETE /database/phases/{phase_id}

**Zweck:** Phase löschen und Streams migrieren

**Code-Referenz:** `unified_service.py:1213-1284`

**URL-Parameter:**
- `phase_id` (int): Phase-ID (1-98)

**Response:**
```json
{
  "status": "success",
  "message": "Phase 2 'Survival Zone' gelöscht. 45 Streams zu Phase 3 verschoben.",
  "deleted_phase_id": 2,
  "affected_streams": 45
}
```

**Migrations-Logik:**
```python
# 1. Nächste Phase finden (höhere ID, < 99)
next_phase = await pool.fetchrow("""
    SELECT id FROM ref_coin_phases
    WHERE id > $1 AND id < 99
    ORDER BY id ASC
    LIMIT 1
""", phase_id)

# 2. Wenn keine nächste Phase → Phase 99 (Finished)
target_phase_id = next_phase['id'] if next_phase else 99

# 3. Streams verschieben
await pool.execute("""
    UPDATE coin_streams
    SET current_phase_id = $1
    WHERE current_phase_id = $2 AND is_active = true
""", target_phase_id, phase_id)
```

**Fehler:**
- `400`: System-Phase (99/100) kann nicht gelöscht werden
- `400`: Mindestens eine reguläre Phase muss bleiben
- `404`: Phase nicht gefunden

**Beispiel-Request:**
```bash
curl -X DELETE http://localhost:3001/api/database/phases/4
```

---

## Database Queries

### GET /database/streams

**Zweck:** Aktive und historische Coin-Streams auflisten

**Code-Referenz:** `unified_service.py:1287-1308`

**Query-Parameter:**
- `limit` (int, default: 50): Maximale Anzahl Ergebnisse

**Response:**
```json
{
  "streams": [
    {
      "id": 1523,
      "token_address": "So11111...",
      "current_phase_id": 1,
      "is_active": true,
      "is_graduated": false,
      "started_at": "2025-01-18T12:00:00Z",
      "ath_price_sol": 0.00001234
    }
  ],
  "count": 50,
  "limit": 50
}
```

**Beispiel-Request:**
```bash
curl "http://localhost:3001/api/database/streams?limit=100"
```

---

### GET /database/streams/stats

**Zweck:** Aggregierte Stream-Statistiken nach Phase

**Code-Referenz:** `unified_service.py:1311-1344`

**Response:**
```json
{
  "total_streams": 1523,
  "active_streams": 229,
  "ended_streams": 1294,
  "streams_by_phase": {
    "1": 45,
    "2": 120,
    "3": 64,
    "99": 890,
    "100": 404
  }
}
```

**SQL-Query:**
```sql
SELECT current_phase_id, COUNT(*) as count
FROM coin_streams
GROUP BY current_phase_id
ORDER BY current_phase_id ASC
```

---

### GET /database/metrics

**Zweck:** Historische Trading-Metriken abrufen

**Code-Referenz:** `unified_service.py:1347-1387`

**Query-Parameter:**
- `limit` (int, default: 100): Maximale Anzahl Ergebnisse
- `mint` (string, optional): Filter nach Token-Adresse

**Response:**
```json
{
  "metrics": [
    {
      "id": 8750,
      "mint": "So11111...",
      "timestamp": "2025-01-18T12:05:00Z",
      "price_open": 0.00001234,
      "price_high": 0.00001345,
      "price_low": 0.00001200,
      "price_close": 0.00001290,
      "volume_sol": 45.5,
      "volume_buy_sol": 30.2,
      "volume_sell_sol": 15.3,
      "num_buys": 23,
      "num_sells": 12,
      "unique_wallets": 18,
      "whale_buys": 2,
      "whale_sells": 1,
      "whale_buy_volume": 3.5,
      "whale_sell_volume": 1.2,
      "dev_sold_sol": 0.0,
      "micro_trades": 5,
      "market_cap_sol": 12345.67
    }
  ],
  "count": 100,
  "limit": 100,
  "mint_filter": null
}
```

**Beispiel-Requests:**
```bash
# Letzte 100 Metriken
curl "http://localhost:3001/api/database/metrics"

# Metriken für spezifischen Coin
curl "http://localhost:3001/api/database/metrics?mint=So11111...&limit=500"
```

---

## Analytics

### GET /analytics/{mint}

**Zweck:** Preis-Performance über verschiedene Zeitfenster

**Code-Referenz:** `unified_service.py:479-503`

**URL-Parameter:**
- `mint` (string): Token-Adresse

**Query-Parameter:**
- `windows` (string, default: "30s,1m,3m,5m,15m,30m,1h"): Komma-separierte Zeitfenster

**Response:**
```json
{
  "mint": "So11111...",
  "current_price": 0.00001234,
  "last_updated": "2025-01-18T22:00:00Z",
  "is_active": true,
  "performance": {
    "1m": {
      "price_change_pct": 5.2,
      "old_price": 0.00001173,
      "trend": "🚀 UP",
      "data_found": true,
      "data_age_seconds": 60
    },
    "5m": {
      "price_change_pct": -2.1,
      "old_price": 0.00001260,
      "trend": "📉 DOWN",
      "data_found": true,
      "data_age_seconds": 300
    },
    "15m": {
      "price_change_pct": 0.0,
      "old_price": null,
      "trend": "➡️ FLAT",
      "data_found": false,
      "data_age_seconds": null
    }
  }
}
```

**Zeitfenster-Parsing:**
```python
def parse_time_windows(windows_str: str) -> dict:
    """Parse '30s,1m,5m' → {'30s': 30, '1m': 60, '5m': 300}"""
    windows = {}
    for w in windows_str.split(','):
        w = w.strip()
        if w.endswith('s'):
            windows[w] = int(w[:-1])
        elif w.endswith('m'):
            windows[w] = int(w[:-1]) * 60
        elif w.endswith('h'):
            windows[w] = int(w[:-1]) * 3600
    return windows
```

**Trend-Berechnung:**
```python
if price_change_pct > 1:
    trend = "🚀 UP"
elif price_change_pct < -1:
    trend = "📉 DOWN"
else:
    trend = "➡️ FLAT"
```

---

## Fehlerbehandlung

Alle Endpunkte verwenden konsistente HTTP-Statuscodes:

| Code | Bedeutung | Beispiel |
|------|-----------|----------|
| 200 | Erfolg | Daten erfolgreich abgerufen |
| 400 | Bad Request | Validierungsfehler, ungültige Parameter |
| 404 | Not Found | Phase/Stream nicht gefunden |
| 500 | Server Error | Datenbank-Fehler, unerwarteter Fehler |
| 503 | Service Unavailable | Datenbank nicht verbunden |

**Fehler-Response-Format:**
```json
{
  "detail": "Phase 99 kann nicht bearbeitet werden"
}
```

---

## CORS-Konfiguration

Alle Endpunkte setzen CORS-Header für Frontend-Zugriff:

```python
headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "*"
}
```

---

## Weiterführende Dokumentation

- [WebSocket-Protokoll](websocket.md) - pumpportal.fun Event-Format
- [Datenfluss](../architecture/data-flow.md) - Wie Daten durch das System fließen
- [Phase Management](../algorithms/phase-management.md) - Lifecycle im Detail

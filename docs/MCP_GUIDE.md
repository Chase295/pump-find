# MCP Server Guide — Pump Find

## Was ist MCP?

Das **Model Context Protocol (MCP)** ist ein offenes Protokoll, das AI-Assistenten standardisierten Zugriff auf externe Tools gibt. Pump Find stellt alle seine REST-Endpoints automatisch als MCP-Tools bereit — ein AI-Assistent kann damit den Service abfragen, konfigurieren und steuern.

## Architektur

```
AI-Client (Claude, Cursor, ...)
    │
    │  Streamable HTTP (POST /mcp)
    ▼
Nginx Reverse Proxy (:3001)
    │
    │  proxy_pass /mcp → :8000/mcp
    ▼
FastAPI Backend (:8000)
    │
    │  fastapi-mcp Library
    ▼
14 MCP-Tools (automatisch aus REST-Endpoints generiert)
```

### Transport: Streamable HTTP

Der MCP-Server nutzt **Streamable HTTP** — den aktuellen Standard für Remote-MCP-Verbindungen.

**Ablauf:**
1. Client sendet `POST /mcp` mit JSON-RPC Request
2. Server verarbeitet den Request und streamt die Antwort zurück
3. Für langlebige Operationen nutzt der Server SSE innerhalb der HTTP-Response

**Vorteile gegenüber dem älteren SSE-Transport:**
- Funktioniert mit Claude.ai (Web), Claude Desktop und Claude Code
- Robuster über das Internet (kein langlebiger GET-Stream nötig)
- Standard-HTTP-Infrastruktur (Proxies, Load Balancer) kompatibel

### Implementierung

```python
from fastapi_mcp import FastApiMCP

mcp = FastApiMCP(
    app,
    name="Pump Finder MCP",
    description="MCP Server für den Pump Finder Crypto-Token Monitoring Service.",
)
mcp.mount_http(mount_path="/mcp")
```

Die `fastapi-mcp` Library liest automatisch alle FastAPI-Routen aus und generiert daraus MCP-Tool-Definitionen mit Namen, Beschreibungen und Parametern.

## Verbindung herstellen

### URLs

| Zugang | URL |
|--------|-----|
| Lokal (direkt) | `http://localhost:8000/mcp` |
| Lokal (via Nginx) | `http://localhost:3001/mcp` |
| Remote (Produktion) | `https://pump-find.chase295.de/mcp` |

### Claude Code

Wird automatisch über `.mcp.json` im Projekt-Root konfiguriert:

```json
{
  "mcpServers": {
    "pump-finder": {
      "type": "streamable-http",
      "url": "http://localhost:3001/mcp"
    }
  }
}
```

### Claude.ai (Web)

1. Claude.ai öffnen (Pro/Max/Team/Enterprise Plan erforderlich)
2. Unter Einstellungen → Integrations → "Add MCP Server"
3. URL eingeben: `https://pump-find.chase295.de/mcp`
4. Name: `Pump Finder`

### Claude Desktop

In der Claude Desktop Konfigurationsdatei:

```json
{
  "mcpServers": {
    "pump-finder": {
      "type": "streamable-http",
      "url": "https://pump-find.chase295.de/mcp"
    }
  }
}
```

---

## MCP-Tools im Detail

### Übersicht

| # | Tool | Methode | Endpoint | Kategorie |
|---|------|---------|----------|-----------|
| 1 | `get_health` | GET | /health | System |
| 2 | `get_metrics` | GET | /metrics | System |
| 3 | `get_config` | GET | /config | Konfiguration |
| 4 | `update_config` | PUT | /config | Konfiguration |
| 5 | `reload_config` | POST | /reload-config | Konfiguration |
| 6 | `list_phases` | GET | /database/phases | Phasen |
| 7 | `create_phase` | POST | /database/phases | Phasen |
| 8 | `update_phase` | PUT | /database/phases/{id} | Phasen |
| 9 | `delete_phase` | DELETE | /database/phases/{id} | Phasen |
| 10 | `get_streams` | GET | /database/streams | Daten |
| 11 | `get_stream_stats` | GET | /database/streams/stats | Daten |
| 12 | `get_recent_metrics` | GET | /database/metrics | Daten |
| 13 | `get_coin_detail` | GET | /database/coins/{mint} | Daten |
| 14 | `get_coin_analytics` | GET | /analytics/{mint} | Daten |

---

### 1. `get_health` — Service-Status abrufen

**Zweck:** Prüft den Zustand aller Subsysteme — WebSocket, Datenbank, Cache, Tracking und Discovery.

**Parameter:** Keine

**Was passiert intern:**
- Führt `SELECT 1` auf der Datenbank aus (echter Verbindungstest)
- Prüft ob die letzte WebSocket-Nachricht < 5 Minuten alt ist
- Sammelt Statistiken aus Cache, Tracking und Discovery
- Berechnet Uptime seit Service-Start

**Antwort:**
```json
{
  "status": "healthy",
  "ws_connected": true,
  "db_connected": true,
  "uptime_seconds": 86400,
  "last_message_ago": 2,
  "reconnect_count": 0,
  "last_error": null,
  "cache_stats": {
    "total_coins": 15,
    "activated_coins": 3,
    "expired_coins": 12,
    "oldest_age_seconds": 118,
    "newest_age_seconds": 5
  },
  "tracking_stats": {
    "active_coins": 620,
    "total_trades": 45000,
    "total_metrics_saved": 12000
  },
  "discovery_stats": {
    "total_coins_discovered": 500,
    "n8n_available": true,
    "n8n_buffer_size": 0
  }
}
```

**Felder erklärt:**
- `status`: `"healthy"` (alles OK) oder `"degraded"` (DB oder WS Problem)
- `last_message_ago`: Sekunden seit der letzten WebSocket-Nachricht
- `reconnect_count`: Wie oft der WebSocket sich reconnecten musste
- `cache_stats.total_coins`: Coins aktuell im 120s-Cache
- `cache_stats.activated_coins`: Coins die vom Cache ins aktive Tracking gewechselt sind
- `tracking_stats.active_coins`: Aktuell aktiv getrackte Coins in der Datenbank
- `discovery_stats.n8n_buffer_size`: Coins die auf den n8n-Webhook warten

**Typische Nutzung:**
> "Wie geht es dem Service?" → `get_health` aufrufen, Status interpretieren

---

### 2. `get_metrics` — Prometheus-Metriken

**Zweck:** Gibt alle Prometheus-Metriken im Textformat zurück.

**Parameter:** Keine

**Antwort:** Plain Text (Prometheus Format)
```
# HELP unified_coins_received_total Total coins received from WebSocket
# TYPE unified_coins_received_total counter
unified_coins_received_total 1234.0
# HELP unified_cache_size Current coins in cache
# TYPE unified_cache_size gauge
unified_cache_size 15.0
# HELP unified_coins_tracked Currently tracked coins
# TYPE unified_coins_tracked gauge
unified_coins_tracked 620.0
...
```

**Wichtige Metriken:**
| Metrik | Typ | Beschreibung |
|--------|-----|-------------|
| `unified_coins_received_total` | Counter | Empfangene Coins seit Start |
| `unified_cache_size` | Gauge | Coins aktuell im Cache |
| `unified_coins_tracked` | Gauge | Aktiv getrackte Coins |
| `unified_trades_received_total` | Counter | Empfangene Trade-Events |
| `unified_metrics_saved_total` | Counter | Gespeicherte Metrik-Einträge |
| `unified_ws_connected` | Gauge | WebSocket-Status (1/0) |
| `unified_db_connected` | Gauge | Datenbank-Status (1/0) |

**Typische Nutzung:**
> "Wie viele Trades wurden verarbeitet?" → `get_metrics` aufrufen, `unified_trades_received_total` auslesen

---

### 3. `get_config` — Konfiguration lesen

**Zweck:** Gibt die aktuelle Runtime-Konfiguration zurück.

**Parameter:** Keine

**Antwort:**
```json
{
  "n8n_webhook_url": "https://n8n.example.com/webhook/...",
  "n8n_webhook_method": "POST",
  "db_dsn": "postgresql://user:***@host:5432/db",
  "coin_cache_seconds": 120,
  "db_refresh_interval": 10,
  "batch_size": 10,
  "batch_timeout": 30,
  "bad_names_pattern": "test|bot|rug|scam|cant|honey|faucet",
  "spam_burst_window": 30,
  "sol_reserves_full": 85.0,
  "whale_threshold_sol": 1.0,
  "age_calculation_offset_min": 60,
  "trade_buffer_seconds": 180,
  "ath_flush_interval": 5
}
```

**Hinweis:** Das Datenbank-Passwort wird aus Sicherheitsgründen mit `***` zensiert.

**Typische Nutzung:**
> "Wie lange bleiben Coins im Cache?" → `get_config` aufrufen, `coin_cache_seconds` lesen

---

### 4. `update_config` — Konfiguration ändern

**Zweck:** Ändert Konfigurationswerte zur Laufzeit ohne Neustart.

**Parameter (alle optional):**
| Parameter | Typ | Bereich | Beschreibung |
|-----------|-----|---------|-------------|
| `n8n_webhook_url` | string | — | Webhook-URL für neue Coins |
| `n8n_webhook_method` | string | GET, POST | HTTP-Methode für Webhook |
| `db_dsn` | string | — | PostgreSQL Connection String |
| `coin_cache_seconds` | int | 10–3600 | Cache-Dauer für neue Coins |
| `db_refresh_interval` | int | 5–300 | DB-Abfrage-Intervall (s) |
| `batch_size` | int | 1–100 | Coins pro n8n-Batch |
| `batch_timeout` | int | 10–300 | Max. Batch-Wartezeit (s) |
| `bad_names_pattern` | string | — | Regex für Spam-Filterung |
| `spam_burst_window` | int | 5–300 | Spam-Erkennungsfenster (s) |

**Beispiel-Aufruf:**
```json
{
  "coin_cache_seconds": 180,
  "batch_size": 20
}
```

**Antwort:**
```json
{
  "status": "success",
  "message": "Konfiguration aktualisiert: coin_cache_seconds, batch_size",
  "updated_fields": ["coin_cache_seconds", "batch_size"],
  "new_config": { ... }
}
```

**Was passiert intern:**
1. Parameter werden validiert (Bereiche, erlaubte Werte)
2. Konfiguration wird in die `.env` Datei geschrieben
3. Globale Variablen werden im laufenden Service aktualisiert
4. Bei Änderung von `db_dsn`: Datenbank-Reconnect wird ausgelöst

**Typische Nutzung:**
> "Setze den Cache auf 3 Minuten" → `update_config` mit `{"coin_cache_seconds": 180}`

---

### 5. `reload_config` — Konfiguration neu laden

**Zweck:** Lädt die Konfiguration aus der `.env` Datei und die Phasen aus der Datenbank neu.

**Parameter:** Keine

**Antwort:**
```json
{
  "status": "success",
  "message": "Konfiguration wurde neu geladen",
  "config": {
    "COIN_CACHE_SECONDS": 120,
    "DB_REFRESH_INTERVAL": 10,
    "BATCH_SIZE": 10
  }
}
```

**Was passiert intern:**
1. `.env` Datei wird neu eingelesen
2. Phasen-Konfiguration wird aus der Datenbank geladen
3. Aktive Streams werden mit neuen Phasen-Einstellungen aktualisiert

**Typische Nutzung:**
> "Lade die Konfiguration neu" → `reload_config` aufrufen

---

### 6. `list_phases` — Alle Phasen auflisten

**Zweck:** Gibt alle definierten Tracking-Phasen zurück.

**Parameter:** Keine

**Antwort:**
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

**Phasen erklärt:**
- **ID 1–98:** Reguläre Phasen (editierbar). `interval_seconds` bestimmt wie oft Metriken gespeichert werden
- **ID 99 (Finished):** Coin hat das maximale Alter überschritten, Tracking gestoppt
- **ID 100 (Graduated):** Coin hat die Bonding Curve verlassen (auf Raydium), Tracking gestoppt

**Typische Nutzung:**
> "Welche Phasen gibt es?" → `list_phases` aufrufen

---

### 7. `create_phase` — Neue Phase erstellen

**Zweck:** Erstellt eine neue Tracking-Phase mit automatischer ID-Vergabe.

**Parameter (alle erforderlich):**
| Parameter | Typ | Beschreibung |
|-----------|-----|-------------|
| `name` | string | Name der Phase |
| `interval_seconds` | int | Metrik-Speicherintervall (min. 1) |
| `min_age_minutes` | int | Minimales Coin-Alter (min. 0) |
| `max_age_minutes` | int | Maximales Coin-Alter (muss > min_age) |

**Beispiel-Aufruf:**
```json
{
  "name": "Extended Zone",
  "interval_seconds": 30,
  "min_age_minutes": 240,
  "max_age_minutes": 480
}
```

**Antwort:**
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

**Was passiert intern:**
1. Nächste freie ID zwischen 1–98 wird gesucht
2. Phase wird in `ref_coin_phases` Tabelle eingefügt
3. Phasen-Konfiguration wird im laufenden Service neu geladen

**Einschränkungen:**
- Maximal 98 reguläre Phasen (ID 1–98)
- `interval_seconds` muss >= 1 sein
- `max_age_minutes` muss > `min_age_minutes` sein

**Typische Nutzung:**
> "Erstelle eine neue Phase für Coins zwischen 4 und 8 Stunden mit 30s Intervall"

---

### 8. `update_phase` — Phase bearbeiten

**Zweck:** Aktualisiert eine bestehende Phase. Löst ein Live-Reload aller betroffenen Streams aus.

**Parameter:**
| Parameter | Wo | Typ | Beschreibung |
|-----------|-----|-----|-------------|
| `phase_id` | Pfad | int | ID der Phase |
| `name` | Body (optional) | string | Neuer Name |
| `interval_seconds` | Body (optional) | int | Neues Intervall (min. 1) |
| `min_age_minutes` | Body (optional) | int | Neues Min-Alter |
| `max_age_minutes` | Body (optional) | int | Neues Max-Alter |

**Beispiel-Aufruf:** Phase 1 Intervall auf 10 Sekunden ändern
```json
// PUT /database/phases/1
{
  "interval_seconds": 10
}
```

**Antwort:**
```json
{
  "status": "success",
  "message": "Phase 1 erfolgreich aktualisiert",
  "phase": {
    "id": 1,
    "name": "Baby Zone",
    "interval_seconds": 10,
    "min_age_minutes": 0,
    "max_age_minutes": 10
  },
  "updated_streams": 45
}
```

**Was passiert intern:**
1. Validierung (System-Phasen 99/100 geschützt, Wertebereiche)
2. Phase in der Datenbank aktualisiert
3. Phasen-Konfiguration im Service neu geladen
4. Alle aktiven Streams in dieser Phase werden mit dem neuen Intervall aktualisiert

**Einschränkungen:**
- System-Phasen (ID >= 99) können nicht bearbeitet werden
- `interval_seconds` muss >= 1 sein
- `max_age_minutes` muss > `min_age_minutes` sein

**Typische Nutzung:**
> "Ändere das Intervall von Phase 1 auf 10 Sekunden" → `update_phase` mit `phase_id=1`, `{"interval_seconds": 10}`

---

### 9. `delete_phase` — Phase löschen

**Zweck:** Löscht eine Phase und migriert alle betroffenen Streams automatisch zur nächsten Phase.

**Parameter:**
| Parameter | Wo | Typ | Beschreibung |
|-----------|-----|-----|-------------|
| `phase_id` | Pfad | int | ID der zu löschenden Phase |

**Antwort:**
```json
{
  "status": "success",
  "message": "Phase 3 'Mature Zone' gelöscht. 12 Streams zu Phase 99 verschoben.",
  "deleted_phase_id": 3,
  "affected_streams": 12
}
```

**Was passiert intern:**
1. Validierung (System-Phasen geschützt, mindestens 1 reguläre Phase muss bleiben)
2. Nächsthöhere Phase wird als Migrationsziel ermittelt (oder Phase 99 falls keine höhere existiert)
3. Alle aktiven Streams in der gelöschten Phase werden zur Zielphase verschoben
4. Phase wird aus der Datenbank gelöscht
5. Phasen-Konfiguration wird neu geladen

**Einschränkungen:**
- System-Phasen (ID >= 99) können nicht gelöscht werden
- Mindestens 1 reguläre Phase muss bestehen bleiben

**Typische Nutzung:**
> "Lösche Phase 3" → `delete_phase` mit `phase_id=3`

---

### 10. `get_streams` — Aktive Coin-Streams

**Zweck:** Gibt die neuesten Coin-Tracking-Streams aus der Datenbank zurück.

**Parameter:**
| Parameter | Wo | Typ | Default | Beschreibung |
|-----------|-----|-----|---------|-------------|
| `limit` | Query | int | 50 | Max. Anzahl Streams |

**Antwort:**
```json
{
  "streams": [
    {
      "id": 1234,
      "token_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
      "current_phase_id": 1,
      "is_active": true,
      "started_at": "2025-01-20T12:00:00Z",
      "graduated_at": null,
      "finished_at": null
    }
  ],
  "count": 50,
  "limit": 50
}
```

**Typische Nutzung:**
> "Zeige mir die letzten 10 Streams" → `get_streams` mit `limit=10`

---

### 11. `get_stream_stats` — Stream-Statistiken

**Zweck:** Aggregierte Statistiken über alle Streams, gruppiert nach Phase.

**Parameter:** Keine

**Antwort:**
```json
{
  "total_streams": 1500,
  "active_streams": 620,
  "ended_streams": 880,
  "streams_by_phase": {
    "1": 200,
    "2": 250,
    "3": 170,
    "99": 500,
    "100": 380
  }
}
```

**Felder erklärt:**
- `total_streams`: Alle Streams jemals erstellt
- `active_streams`: Aktuell aktiv (`is_active = true`)
- `ended_streams`: Beendet (`is_active = false`)
- `streams_by_phase`: Verteilung auf die Phasen

**Typische Nutzung:**
> "Wie viele Coins werden gerade getrackt?" → `get_stream_stats` aufrufen, `active_streams` lesen

---

### 12. `get_recent_metrics` — Letzte Metriken

**Zweck:** Gibt die neuesten gespeicherten Metriken aus der Datenbank zurück. Optional filterbar nach Coin.

**Parameter:**
| Parameter | Wo | Typ | Default | Beschreibung |
|-----------|-----|-----|---------|-------------|
| `limit` | Query | int | 100 | Max. Anzahl Metriken |
| `mint` | Query | string | — | Filter nach Token-Adresse |

**Antwort:**
```json
{
  "metrics": [
    {
      "id": 5678,
      "mint": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
      "timestamp": "2025-01-20T12:30:00Z",
      "phase_id_at_time": 1,
      "price_open": 0.00001200,
      "price_high": 0.00001500,
      "price_low": 0.00001100,
      "price_close": 0.00001350,
      "market_cap_close": 1200.5,
      "bonding_curve_pct": 45.2,
      "volume_sol": 25.5,
      "buy_volume_sol": 15.0,
      "sell_volume_sol": 10.5,
      "num_buys": 50,
      "num_sells": 30,
      "unique_wallets": 45,
      "dev_sold_amount": 0.0,
      "whale_buy_volume_sol": 5.0
    }
  ],
  "count": 100,
  "limit": 100,
  "mint_filter": null
}
```

**Metriken erklärt:**
| Feld | Beschreibung |
|------|-------------|
| `price_open/high/low/close` | OHLCV-Preise in SOL pro Token |
| `market_cap_close` | Market Cap in SOL zum Zeitpunkt |
| `bonding_curve_pct` | Fortschritt der Bonding Curve (%) |
| `volume_sol` | Gesamtvolumen in SOL |
| `buy_volume_sol` / `sell_volume_sol` | Kauf-/Verkaufsvolumen |
| `num_buys` / `num_sells` | Anzahl Kauf-/Verkaufs-Transaktionen |
| `unique_wallets` | Anzahl verschiedener Wallets |
| `dev_sold_amount` | Vom Ersteller verkaufte Menge |
| `whale_buy_volume_sol` | Kauf-Volumen von Whales (> 1 SOL) |

**Typische Nutzung:**
> "Zeige mir die Metriken für Coin XYZ" → `get_recent_metrics` mit `mint="XYZ..."`

---

### 13. `get_coin_detail` — Vollständige Coin-Details

**Zweck:** Gibt alle verfügbaren Daten zu einem einzelnen Coin zurück — Stammdaten, Stream-Info, letzte Metriken und Live-Tracking-Daten.

**Parameter:**
| Parameter | Wo | Typ | Beschreibung |
|-----------|-----|-----|-------------|
| `mint` | Pfad | string | Token Mint-Adresse |

**Antwort:**
```json
{
  "coin": {
    "token_address": "7xKXtg...",
    "name": "Cool Token",
    "symbol": "COOL",
    "creator_wallet": "Abc123...",
    "discovered_at": "2025-01-20T12:00:00Z",
    "initial_market_cap_sol": 30.0,
    "risk_score": 500,
    "has_socials": true,
    "social_count": 2,
    "twitter": "https://twitter.com/cooltoken",
    "telegram": null,
    "website": "https://cooltoken.io"
  },
  "stream": {
    "id": 1234,
    "token_address": "7xKXtg...",
    "current_phase_id": 1,
    "phase_name": "Baby Zone",
    "is_active": true,
    "started_at": "2025-01-20T12:02:00Z"
  },
  "latest_metrics": {
    "price_close": 0.00001350,
    "volume_sol": 25.5,
    "unique_wallets": 45,
    "timestamp": "2025-01-20T12:30:00Z"
  },
  "live_tracking": {
    "price_open": 0.00001350,
    "price_high": 0.00001600,
    "price_low": 0.00001300,
    "price_close": 0.00001550,
    "volume_sol": 8.2,
    "buy_volume_sol": 5.1,
    "sell_volume_sol": 3.1,
    "num_buys": 12,
    "num_sells": 8,
    "unique_wallets": 15,
    "market_cap_sol": 1400.0,
    "interval_seconds": 5,
    "next_flush_seconds": 2.3
  }
}
```

**Datenquellen:**
| Feld | Quelle |
|------|--------|
| `coin` | `discovered_coins` Tabelle — Stammdaten bei Entdeckung |
| `stream` | `coin_streams` Tabelle — Tracking-Status und Phase |
| `latest_metrics` | `coin_metrics` Tabelle — Letzter gespeicherter Datenpunkt |
| `live_tracking` | In-Memory Watchlist — Echtzeit-Buffer (noch nicht in DB) |

**Besonderheiten:**
- `live_tracking` ist nur vorhanden wenn der Coin gerade aktiv getrackt wird
- `next_flush_seconds` zeigt wann der aktuelle Buffer in die DB geschrieben wird
- Gibt 404 zurück wenn der Coin nicht in `discovered_coins` existiert

**Typische Nutzung:**
> "Zeige mir alles über Coin XYZ" → `get_coin_detail` mit `mint="XYZ..."`

---

### 14. `get_coin_analytics` — Performance-Analyse

**Zweck:** Analysiert die Preis-Performance eines Coins über verschiedene Zeitfenster.

**Parameter:**
| Parameter | Wo | Typ | Default | Beschreibung |
|-----------|-----|-----|---------|-------------|
| `mint` | Pfad | string | — | Token Mint-Adresse |
| `windows` | Query | string | `"30s,1m,3m,5m,15m,30m,1h"` | Komma-getrennte Zeitfenster |

**Zeitfenster-Format:** Zahl + Suffix (`s`=Sekunden, `m`=Minuten, `h`=Stunden)

**Antwort:**
```json
{
  "mint": "7xKXtg...",
  "current_price": 0.00001550,
  "last_updated": "2025-01-20T12:35:00Z",
  "is_active": true,
  "performance": {
    "1m": {
      "price_change_pct": 5.2,
      "old_price": 0.00001473,
      "trend": "PUMP",
      "data_found": true,
      "data_age_seconds": 58
    },
    "5m": {
      "price_change_pct": -2.1,
      "old_price": 0.00001583,
      "trend": "DUMP",
      "data_found": true,
      "data_age_seconds": 295
    },
    "1h": {
      "price_change_pct": 0.3,
      "old_price": 0.00001545,
      "trend": "FLAT",
      "data_found": true,
      "data_age_seconds": 3580
    }
  }
}
```

**Trends:**
| Trend | Bedeutung |
|-------|-----------|
| `PUMP` | Preis steigt |
| `DUMP` | Preis fällt |
| `FLAT` | Preis stabil |

**Typische Nutzung:**
> "Wie hat sich Coin XYZ in den letzten 5 Minuten entwickelt?" → `get_coin_analytics` mit `mint="XYZ..."`, `windows="5m"`

---

## Fehlerbehandlung

Alle Tools geben bei Fehlern HTTP-Statuscodes zurück:

| Code | Bedeutung | Beispiel |
|------|-----------|---------|
| 400 | Ungültige Parameter | `interval_seconds` < 1 |
| 404 | Nicht gefunden | Coin oder Phase existiert nicht |
| 500 | Interner Fehler | Unerwarteter Serverfehler |
| 503 | Service nicht verfügbar | Datenbank nicht verbunden |

**Fehler-Format:**
```json
{
  "detail": "Phase 99 ist eine System-Phase und kann nicht bearbeitet werden"
}
```

## Beispiel-Konversationen

### Service-Status prüfen
```
User: "Ist der Service gesund?"
→ AI ruft get_health auf
→ "Der Service läuft seit 24 Stunden. WebSocket und Datenbank sind verbunden.
   620 Coins werden aktiv getrackt, 15 sind im Cache."
```

### Konfiguration ändern
```
User: "Setze den Cache auf 3 Minuten und die Batch-Größe auf 20"
→ AI ruft update_config auf mit {"coin_cache_seconds": 180, "batch_size": 20}
→ "Cache auf 180 Sekunden und Batch-Größe auf 20 geändert."
```

### Coin analysieren
```
User: "Was weißt du über den Coin 7xKXtg...?"
→ AI ruft get_coin_detail auf
→ "Cool Token (COOL) wurde vor 35 Minuten entdeckt. Er ist in Phase 1 (Baby Zone),
   aktueller Preis: 0.0000155 SOL, 45 verschiedene Wallets haben gehandelt."

User: "Wie hat er sich entwickelt?"
→ AI ruft get_coin_analytics auf mit windows="1m,5m,15m"
→ "In der letzten Minute +5.2% (PUMP), über 5 Minuten -2.1% (DUMP),
   über 15 Minuten +0.3% (FLAT). Der kurzfristige Anstieg folgt auf einen Rückgang."
```

### Phasen verwalten
```
User: "Erstelle eine Phase für Coins zwischen 4-8 Stunden mit 60s Intervall"
→ AI ruft create_phase auf mit {"name": "Extended Zone", "interval_seconds": 60,
   "min_age_minutes": 240, "max_age_minutes": 480}
→ "Phase 4 'Extended Zone' erstellt. Coins zwischen 4-8 Stunden werden
   jetzt alle 60 Sekunden getrackt."
```

## Nginx-Konfiguration

Der MCP-Endpoint wird über Nginx mit speziellen Settings für Streaming proxied:

```nginx
location /mcp {
    proxy_pass http://pump-find-backend:8000/mcp;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 86400s;
    proxy_send_timeout 86400s;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    gzip off;
}
```

**Warum diese Settings:**
- `proxy_buffering off` — Streaming-Antworten sofort weiterleiten
- `proxy_cache off` — Keine Caching von dynamischen MCP-Antworten
- `proxy_read_timeout 86400s` — 24h Timeout für langlebige Verbindungen
- `gzip off` — Kompression ist inkompatibel mit Streaming

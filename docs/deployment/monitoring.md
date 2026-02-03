# Prometheus Monitoring

Dokumentation aller 50+ Prometheus-Metriken.

---

## Übersicht

Das System exportiert Metriken im Prometheus-Format unter:

```
GET /api/metrics
```

**Response:** `text/plain` (Prometheus Format)

---

## Metriken-Kategorien

### Discovery-Metriken

| Metrik | Typ | Beschreibung |
|--------|-----|--------------|
| `unified_coins_received_total` | Counter | Alle empfangenen Coins (vor Filter) |
| `unified_coins_filtered_total{reason="..."}` | Counter | Gefilterte Coins (Labels: bad_name, spam_burst) |
| `unified_coins_sent_n8n_total` | Counter | An n8n gesendete Coins |
| `unified_n8n_batches_sent_total` | Counter | Gesendete n8n-Batches |
| `unified_n8n_buffer_size` | Gauge | Coins im n8n-Discovery-Buffer |
| `unified_n8n_errors_total{type="..."}` | Counter | n8n-Fehler nach Typ |
| `unified_buffer_size` | Gauge | Aktuelle Buffer-Größe |

### Cache-Metriken

| Metrik | Typ | Beschreibung |
|--------|-----|--------------|
| `unified_cache_size` | Gauge | Coins im 120s-Cache |
| `unified_cache_activations_total` | Counter | Cache-Aktivierungen (>= 3 Trades) |
| `unified_cache_expirations_total` | Counter | Cache-Expirations (120s ohne Aktivierung) |

### Trade-Metriken

| Metrik | Typ | Beschreibung |
|--------|-----|--------------|
| `unified_trades_received_total` | Counter | Alle empfangenen Trades |
| `unified_trades_processed_total` | Counter | Verarbeitete Trades (aktive Coins) |
| `unified_metrics_saved_total` | Counter | Gespeicherte Metrik-Einträge |
| `unified_last_trade_timestamp` | Gauge | Unix-Timestamp des letzten Trades |

### Tracking-Metriken

| Metrik | Typ | Beschreibung |
|--------|-----|--------------|
| `unified_coins_tracked` | Gauge | Aktuell getrackte Coins |
| `unified_coins_graduated_total` | Counter | Graduierte Coins (Raydium) |
| `unified_coins_finished_total` | Counter | Beendete Coins (Timeout) |
| `unified_phase_switches_total` | Counter | Phasen-Wechsel |

### Verbindungs-Metriken

| Metrik | Typ | Beschreibung |
|--------|-----|--------------|
| `unified_ws_connected` | Gauge | WebSocket-Status (1=verbunden, 0=getrennt) |
| `unified_db_connected` | Gauge | DB-Status (1=verbunden, 0=getrennt) |
| `unified_ws_reconnects_total` | Counter | WebSocket-Reconnects |
| `unified_uptime_seconds` | Gauge | Service-Uptime |
| `unified_connection_duration_seconds` | Gauge | Aktuelle Verbindungsdauer |

### Batching-Metriken

| Metrik | Typ | Beschreibung |
|--------|-----|--------------|
| `unified_pending_subscriptions` | Gauge | Wartende Subscription-Requests |
| `unified_batches_sent_total` | Counter | Gesendete Subscription-Batches |
| `unified_subscriptions_batched_total` | Counter | Via Batch abonnierte Coins |
| `unified_batch_size` | Histogram | Batch-Größen-Verteilung |

### ATH-Metriken

| Metrik | Typ | Beschreibung |
|--------|-----|--------------|
| `unified_ath_updates_total` | Counter | ATH-Updates in DB |
| `unified_ath_cache_size` | Gauge | Coins im ATH-Cache |

### Performance-Metriken

| Metrik | Typ | Beschreibung |
|--------|-----|--------------|
| `unified_db_query_duration_seconds` | Histogram | Dauer von DB-Queries |
| `unified_flush_duration_seconds` | Histogram | Dauer von Metric-Flushes |
| `unified_db_errors_total{type="..."}` | Counter | DB-Fehler nach Typ |

---

## Code-Referenz

**Definiert in:** `unified_service.py:139-182`

```python
from prometheus_client import Counter as PromCounter, Gauge, Histogram

# Discovery
coins_received = PromCounter("unified_coins_received_total", "Anzahl empfangener Coins")
coins_filtered = PromCounter("unified_coins_filtered_total", "Anzahl gefilterter Coins", ["reason"])
coins_sent_n8n = PromCounter("unified_coins_sent_n8n_total", "Anzahl an n8n gesendeter Coins")

# Cache
cache_size = Gauge("unified_cache_size", "Anzahl Coins im 120s Cache")
cache_activations = PromCounter("unified_cache_activations_total", "Cache-Aktivierungen")
cache_expirations = PromCounter("unified_cache_expirations_total", "Cache-Abläufe")

# Tracking
trades_received = PromCounter("unified_trades_received_total", "Anzahl empfangener Trades")
trades_processed = PromCounter("unified_trades_processed_total", "Anzahl verarbeiteter Trades")
metrics_saved = PromCounter("unified_metrics_saved_total", "Anzahl gespeicherter Metriken")
coins_tracked = Gauge("unified_coins_tracked", "Anzahl aktuell getrackter Coins")

# Verbindungen
ws_connected = Gauge("unified_ws_connected", "WebSocket Status (1=connected)")
db_connected = Gauge("unified_db_connected", "DB Status (1=connected)")
uptime_seconds = Gauge("unified_uptime_seconds", "Uptime in Sekunden")

# Performance
db_query_duration = Histogram("unified_db_query_duration_seconds", "Dauer von DB-Queries")
flush_duration = Histogram("unified_flush_duration_seconds", "Dauer von Metric-Flushes")
```

---

## Beispiel-Output

```prometheus
# HELP unified_coins_received_total Anzahl empfangener Coins
# TYPE unified_coins_received_total counter
unified_coins_received_total 1523.0

# HELP unified_coins_filtered_total Anzahl gefilterter Coins
# TYPE unified_coins_filtered_total counter
unified_coins_filtered_total{reason="bad_name"} 145.0
unified_coins_filtered_total{reason="spam_burst"} 23.0

# HELP unified_cache_size Anzahl Coins im 120s Cache
# TYPE unified_cache_size gauge
unified_cache_size 45.0

# HELP unified_coins_tracked Anzahl aktuell getrackter Coins
# TYPE unified_coins_tracked gauge
unified_coins_tracked 229.0

# HELP unified_ws_connected WebSocket Status (1=connected)
# TYPE unified_ws_connected gauge
unified_ws_connected 1.0

# HELP unified_db_connected DB Status (1=connected)
# TYPE unified_db_connected gauge
unified_db_connected 1.0

# HELP unified_uptime_seconds Uptime in Sekunden
# TYPE unified_uptime_seconds gauge
unified_uptime_seconds 3600.0
```

---

## Grafana Dashboard

### Service Health Panel

```
# Query: Service Status
unified_ws_connected + unified_db_connected

# Thresholds
2 = Healthy (green)
1 = Degraded (yellow)
0 = Unhealthy (red)
```

### Discovery Rate Panel

```
# Query: Coins/Minute
rate(unified_coins_received_total[5m]) * 60

# Query: Filter Rate
rate(unified_coins_filtered_total[5m]) * 60
```

### Trade Volume Panel

```
# Query: Trades/Second
rate(unified_trades_processed_total[1m])
```

### Cache Efficiency Panel

```
# Query: Activation Rate (%)
rate(unified_cache_activations_total[5m]) /
rate(unified_coins_received_total[5m]) * 100
```

### Phase Distribution Panel

```
# Query: Coins per Phase (aus /database/streams/stats)
# Muss via Custom Exporter oder API-Polling implementiert werden
```

---

## Alerting Rules (Prometheus)

### Service Down

```yaml
groups:
  - name: pump-finder
    rules:
      - alert: PumpFinderDown
        expr: unified_ws_connected == 0 or unified_db_connected == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pump Finder service is down"
```

### High Error Rate

```yaml
      - alert: HighFilterRate
        expr: rate(unified_coins_filtered_total[5m]) / rate(unified_coins_received_total[5m]) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "More than 50% of coins are filtered"
```

### No Trades

```yaml
      - alert: NoTradesReceived
        expr: rate(unified_trades_received_total[5m]) == 0
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "No trades received for 15 minutes"
```

### Low Activation Rate

```yaml
      - alert: LowActivationRate
        expr: rate(unified_cache_activations_total[15m]) / rate(unified_coins_received_total[15m]) < 0.1
        for: 30m
        labels:
          severity: info
        annotations:
          summary: "Less than 10% of coins are activated"
```

---

## Metriken im Code verwenden

### Counter erhöhen

```python
# Einfach
coins_received.inc()

# Mit Wert
coins_sent_n8n.inc(len(batch))

# Mit Labels
coins_filtered.labels(reason="bad_name").inc()
```

### Gauge setzen

```python
# Absoluter Wert
cache_size.set(len(self.coin_cache.cache))
ws_connected.set(1)

# Relativ
coins_tracked.set(len(self.watchlist))
```

### Histogram beobachten

```python
# Zeit messen
with db_query_duration.time():
    await self.pool.execute(query)

# Oder manuell
start = time.time()
# ... Operation
db_query_duration.observe(time.time() - start)
```

---

## Scrape-Konfiguration (Prometheus)

```yaml
scrape_configs:
  - job_name: 'pump-finder'
    scrape_interval: 15s
    static_configs:
      - targets: ['pump-finder:3001']
    metrics_path: '/api/metrics'
```

---

## Wichtige Metriken für Debugging

### Verbindungsstatus

```bash
curl -s http://localhost:3001/api/metrics | grep -E "ws_connected|db_connected"
```

### Discovery-Rate

```bash
curl -s http://localhost:3001/api/metrics | grep coins_received_total
```

### Aktive Streams

```bash
curl -s http://localhost:3001/api/metrics | grep coins_tracked
```

### Cache-Status

```bash
curl -s http://localhost:3001/api/metrics | grep cache_
```

---

## Weiterführende Dokumentation

- [Docker Deployment](docker.md) - Container-Konfiguration
- [API-Endpunkte](../api/endpoints.md) - /metrics Endpoint
- [Backend-Architektur](../architecture/backend.md) - Metriken-Integration

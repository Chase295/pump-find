# 🚀 Unified Pump Service

**Vereinter Pump-Discover und Pump-Metric Service mit FastAPI**

Dieses Projekt kombiniert die Funktionalität von pump-discover und pump-metric in einem einzigen Service, der nur eine WebSocket-Verbindung zu pumpportal.fun benötigt.

## 📁 Projekt-Struktur

```
├── unified_service.py          # Haupt-Service (FastAPI)
├── docker-compose.unified.yml   # Docker-Deployment
├── Dockerfile.unified          # Docker-Image
├── requirements.unified.txt    # Python-Dependencies
├── config/                     # Konfigurationsdateien
├── sql/                        # Datenbank-Schema
├── test_unified_service.py     # Unit-Tests
├── README.unified.md           # Vollständige Dokumentation
└── README.md                   # Diese Datei
```

## 🚀 Schnellstart

```bash
# 1. Konfiguration in config/.env anpassen
# 2. Service starten
docker-compose -f docker-compose.unified.yml up -d

# 3. Services prüfen
curl http://localhost:8000/health              # Health-Status
open http://localhost:8000/docs               # API-Dokumentation
curl http://localhost:8000/metrics            # Prometheus-Metriken
```

## 🔌 Port-Konfiguration

| Service | Port | Beschreibung |
|---------|------|--------------|
| **FastAPI Service** | 8000 | API, Health-Checks, Metriken, Konfiguration |

## 📚 Dokumentation

- **[README.unified.md](README.unified.md)** - Vollständige Setup-Anleitung
- **[SQL Schema](sql/schema.sql)** - Datenbankschema
- **API-Dokumentation:** `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs:** `http://localhost:8000/redoc`

## 🏗️ Features

### ✅ Vereinte Funktionalität
- **Coin-Discovery**: Neue Tokens über WebSocket empfangen
- **Filtering**: Bad Names, Spam-Burst Filter
- **n8n Integration**: Gefilterte Tokens an n8n senden
- **Metric-Tracking**: Aktive Coins tracken und Metriken speichern
- **Cache-System**: 120s Cache für neue Coins
- **Automatische Verwaltung**: Coin-Streams werden automatisch aktiviert

### ✅ Moderne API
- **FastAPI** mit automatischer Dokumentation
- **Pydantic-Modelle** für Type-Safety
- **RESTful Endpoints** für Konfiguration
- **Prometheus-Metriken** integriert
- **Health-Checks** mit detaillierten Status

### ✅ Production-Ready
- **Docker-Containerisierung**
- **uvicorn ASGI-Server**
- **Persistente Konfiguration**
- **Robuste Fehlerbehandlung**

## 📊 Datenfluss

```
Pump.fun WebSocket
    ├── subscribeNewToken → Neue Coins empfangen
    │   ├── Filter anwenden (Bad Names, Spam)
    │   ├── Coin in 120s Cache legen
    │   ├── Sofort für Trades abonnieren
    │   └── An n8n senden (gefilterte Coins)
    │
    └── subscribeTokenTrade → Trades empfangen
        ├── Coin aktiv? → Sofort verarbeiten
        ├── Coin im Cache? → Trade sammeln
        └── Metriken in DB speichern
```

## 🛠️ Technologie-Stack

- **Python 3.11** - FastAPI Service
- **FastAPI + Pydantic** - Moderne Web-API
- **uvicorn** - ASGI-Server
- **websockets + httpx** - Netzwerk-Kommunikation
- **asyncpg** - PostgreSQL-Client
- **Docker Compose** - Container-Orchestrierung

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "ws_connected": true,
  "db_connected": true,
  "uptime_seconds": 3600,
  "cache_stats": {
    "total_coins": 25,
    "activated_coins": 3,
    "expired_coins": 22
  },
  "tracking_stats": {
    "active_coins": 8,
    "total_trades": 15420
  },
  "discovery_stats": {
    "total_coins_discovered": 234,
    "n8n_available": true
  }
}
```

### Konfiguration verwalten
```bash
# Aktuelle Konfiguration abrufen
GET /config

# Konfiguration aktualisieren
PUT /config
Content-Type: application/json

{
  "n8n_webhook_url": "https://mein-n8n-server.com/webhook/xyz",
  "db_dsn": "postgresql://user:pass@host:port/db",
  "coin_cache_seconds": 300
}
```

### Prometheus Metriken
```bash
GET /metrics
```

**Wichtige Metriken:**
- `unified_coins_received_total` - Empfangene Coins
- `unified_cache_size` - Coins im Cache
- `unified_coins_tracked` - Aktive Coins
- `unified_trades_received_total` - Trade-Events
- `unified_metrics_saved_total` - Gespeicherte Metriken
- `unified_ws_connected` - WebSocket-Status
- `unified_db_connected` - Datenbank-Status

## 🔧 Konfiguration

Die Konfiguration wird in `config/.env` gespeichert und kann über die API geändert werden:

```bash
# n8n-Server ändern
curl -X PUT http://localhost:8000/config \
  -H "Content-Type: application/json" \
  -d '{"n8n_webhook_url": "https://neuer-server.com/webhook"}'

# Datenbank wechseln
curl -X PUT http://localhost:8000/config \
  -H "Content-Type: application/json" \
  -d '{"db_dsn": "postgresql://user:pass@newhost:5432/newdb"}'
```

## 📝 Lizenz

Siehe LICENSE Datei (falls vorhanden).


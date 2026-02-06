# Pump Find

Solana-Token Monitoring Service — Discovery, Metrics-Tracking und React-UI in einem integrierten System. Überwacht neue Tokens auf der Solana-Blockchain via [pump.fun](https://pump.fun).

## Architektur

Pump Find besteht aus zwei Docker-Services hinter einem gemeinsamen Nginx Reverse Proxy:

```
                         ┌─────────────────────────────────┐
                         │       pump-find-frontend         │
  Browser ──── :3001 ──▶ │  Nginx (React SPA + Reverse Proxy) │
                         │                                  │
                         │   /        → React UI            │
                         │   /api/*   → Backend             │
                         │   /api/mcp → Backend (SSE)       │
                         └──────────────┬───────────────────┘
                                        │ Docker Network
                         ┌──────────────▼───────────────────┐
                         │       pump-find-backend           │
                         │  FastAPI (uvicorn :8000)          │
                         │                                   │
                         │   WebSocket ◀── pumpportal.fun    │
                         │   asyncpg   ──▶ PostgreSQL        │
                         │   httpx     ──▶ n8n Webhook       │
                         └───────────────────────────────────┘
```

Nur Port **3001** ist extern exponiert. Das Backend ist ausschließlich über das Docker-Network erreichbar.

## Schnellstart

```bash
# .env Datei anlegen
cp .env.example .env
# Werte in .env anpassen (DB_DSN, N8N_WEBHOOK_URL)

# Stack starten
docker compose up -d

# Health prüfen
curl http://localhost:3001/api/health

# UI öffnen
open http://localhost:3001

# API-Docs (Swagger UI)
open http://localhost:3001/api/docs
```

## Projekt-Struktur

```
├── backend/                    # Python Backend
│   ├── Dockerfile              # Backend Docker-Image
│   ├── requirements.txt        # Python-Dependencies
│   ├── requirements.test.txt   # Test-Dependencies (pytest)
│   ├── pytest.ini              # pytest-Konfiguration
│   ├── unified_service.py      # Haupt-Service (FastAPI, Discovery, Metrics)
│   ├── db_migration.py         # Datenbank-Schema Initialisierung
│   └── tests/                  # Backend-Tests (201 Tests)
│       ├── unit/               # Unit-Tests
│       ├── integration/        # Integrations-Tests
│       └── stress/             # Stress-/Last-Tests
├── frontend/                   # React TypeScript Frontend
│   ├── Dockerfile              # Frontend Docker-Image (Nginx)
│   ├── nginx.conf              # Nginx Reverse Proxy Konfiguration
│   ├── src/
│   │   ├── pages/              # Dashboard, Metrics, Phases, Config, Logs, Info
│   │   ├── stores/pumpStore.ts # Zustand State Management
│   │   ├── services/api.ts     # Axios HTTP Client
│   │   ├── types/api.ts        # TypeScript Interfaces
│   │   └── __tests__/          # Frontend-Tests (101 Tests)
│   └── vitest.config.ts        # Vitest-Konfiguration
├── docs/                       # Zusätzliche Dokumentation
├── sql/                        # Datenbank-Schema
├── scripts/                    # Test-Utilities
├── config/                     # Runtime-Konfiguration
├── docker-compose.yaml         # Full-Stack Orchestrierung
├── .env.example                # Vorlage für Umgebungsvariablen
└── .mcp.json                   # MCP-Client Konfiguration
```

## Tech-Stack

| Schicht | Technologien |
|---------|-------------|
| **Backend** | Python 3.11, FastAPI, asyncpg, websockets, httpx, Pydantic |
| **Frontend** | React 18, TypeScript, Vite, Material-UI, Zustand |
| **Testing** | pytest (Backend), vitest + MSW (Frontend) |
| **Deployment** | Docker Compose, Nginx Reverse Proxy |
| **AI-Integration** | fastapi-mcp (Model Context Protocol) |

## Port-Konfiguration

| Service | Port | Beschreibung |
|---------|------|--------------|
| pump-find-frontend (Nginx) | 3001 | UI + API Reverse Proxy (extern) |
| pump-find-backend (FastAPI) | 8000 | API-Server (nur intern via Docker-Network) |

## API Endpoints

Alle Endpoints sind über `http://localhost:3001/api/` erreichbar.

### Health & Monitoring

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/health` | Service-Health mit detaillierten Stats |
| GET | `/metrics` | Prometheus-Metriken |

### Konfiguration

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/config` | Aktuelle Service-Konfiguration |
| PUT | `/config` | Konfiguration zur Laufzeit ändern |
| POST | `/reload-config` | Konfiguration und Phasen neu laden |

### Phasen-Management (CRUD)

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/database/phases` | Alle Tracking-Phasen auflisten |
| POST | `/database/phases` | Neue Phase erstellen (ID 1–98) |
| PUT | `/database/phases/{id}` | Phase bearbeiten (Live-Reload) |
| DELETE | `/database/phases/{id}` | Phase löschen (Streams migrieren automatisch) |

### Datenbank & Streams

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/database/streams` | Aktive Coin-Tracking Streams |
| GET | `/database/streams/stats` | Stream-Statistiken nach Phase |
| GET | `/database/metrics` | Letzte Metriken aus der Datenbank |
| GET | `/database/coins/{mint}` | Vollständige Coin-Details |
| GET | `/analytics/{mint}` | Coin-Performance-Analyse (mit Zeitfenstern) |

## Datenfluss

```
pumpportal.fun WebSocket
    │
    ├── subscribeNewToken → Neue Coins empfangen
    │   ├── Filter anwenden (Bad Names, Spam-Burst)
    │   ├── Coin in 120s Cache legen
    │   ├── Sofort für Trades abonnieren
    │   └── An n8n Webhook senden
    │
    └── subscribeTokenTrade → Trades empfangen
        ├── Coin aktiv? → Sofort Metriken verarbeiten
        ├── Coin im Cache? → Trades sammeln
        └── Nach Cache-Ablauf → Stream aktivieren, Metriken in DB speichern
```

## Phasen-System

Coins durchlaufen Tracking-Phasen basierend auf ihrem Alter. Jede Phase definiert das Speicherintervall und den Altersbereich.

### Standard-Phasen

| ID | Name | Intervall | Min. Alter | Max. Alter |
|----|------|-----------|------------|------------|
| 1 | Baby Zone | 5s | 0 min | 10 min |
| 2 | Survival Zone | 15s | 10 min | 120 min |
| 3 | Mature Zone | 15s | 120 min | 240 min |
| 99 | Finished | — | — | — |
| 100 | Graduated | — | — | — |

- **System-Phasen** (99, 100) sind geschützt und können nicht geändert werden
- Beim Löschen einer Phase werden aktive Streams automatisch in die nächste Phase migriert
- Phase-Änderungen lösen ein Live-Reload der betroffenen Streams aus

## MCP Server (Model Context Protocol)

### Was ist MCP?

Das [Model Context Protocol](https://modelcontextprotocol.io/) ist ein offenes Protokoll, das AI-Assistenten (wie Claude) standardisiert Zugriff auf externe Tools und Datenquellen gibt. Pump Find exponiert alle REST-Endpoints als MCP-Tools — AI-Assistenten können dadurch direkt mit dem Service interagieren.

### Implementierung

Pump Find nutzt die [`fastapi-mcp`](https://github.com/tadata-org/fastapi-mcp) Library, die automatisch alle FastAPI-Endpoints als MCP-Tools bereitstellt. Der Transport erfolgt über **SSE (Server-Sent Events)**.

```python
from fastapi_mcp import FastApiMCP

mcp = FastApiMCP(
    app,
    name="Pump Finder MCP",
    description="MCP Server für den Pump Finder Crypto-Token Monitoring Service.",
)
mcp.mount_sse(mount_path="/mcp")
```

### Zugang

| Zugang | URL |
|--------|-----|
| Direkt (intern) | `http://localhost:8000/mcp` |
| Via Nginx (extern) | `http://localhost:3001/api/mcp` |

### Verfügbare MCP-Tools

Jeder REST-Endpoint wird automatisch als MCP-Tool exponiert:

| Tool | Endpoint | Beschreibung |
|------|----------|--------------|
| `get_health` | GET /health | Service-Health mit detaillierten Stats |
| `get_metrics` | GET /metrics | Prometheus-Metriken |
| `get_config` | GET /config | Aktuelle Konfiguration lesen |
| `update_config` | PUT /config | Konfiguration zur Laufzeit ändern |
| `reload_config` | POST /reload-config | Konfiguration und Phasen neu laden |
| `list_phases` | GET /database/phases | Alle Tracking-Phasen auflisten |
| `create_phase` | POST /database/phases | Neue Phase erstellen |
| `update_phase` | PUT /database/phases/{id} | Phase bearbeiten (Live-Reload) |
| `delete_phase` | DELETE /database/phases/{id} | Phase löschen (Streams migrieren) |
| `get_streams` | GET /database/streams | Aktive Coin-Streams |
| `get_stream_stats` | GET /database/streams/stats | Stream-Statistiken nach Phase |
| `get_recent_metrics` | GET /database/metrics | Letzte Metriken aus DB |
| `get_coin_detail` | GET /database/coins/{mint} | Vollständige Coin-Details |
| `get_coin_analytics` | GET /analytics/{mint} | Coin-Performance-Analyse |

### Client-Konfiguration

Die Datei `.mcp.json` im Projekt-Root konfiguriert kompatible AI-Clients automatisch:

```json
{
  "mcpServers": {
    "pump-finder": {
      "type": "sse",
      "url": "http://localhost:3001/api/mcp"
    }
  }
}
```

### Kompatible Clients

| Client | Konfiguration |
|--------|--------------|
| **Claude Code** | Liest `.mcp.json` automatisch aus dem Projekt-Root |
| **Claude Desktop** | MCP-Server manuell in den Einstellungen hinzufügen |
| **Cursor** | MCP-Server in den Cursor-Settings konfigurieren |

### Nginx SSE Proxy

Der Nginx Reverse Proxy hat spezielle Settings für den SSE-Transport des MCP-Servers:

```nginx
location /api/mcp {
    proxy_pass http://pump-find-backend:8000/mcp;

    # SSE-spezifisch
    proxy_buffering off;     # Kein Buffering von SSE-Streams
    proxy_cache off;         # Kein Caching
    proxy_read_timeout 86400s;  # 24h Timeout für langlebige Verbindungen
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    gzip off;                # Kompression inkompatibel mit SSE
}
```

### Beispiel-Nutzung

Ein AI-Assistent kann über MCP z.B. folgende Aktionen ausführen:

```
User: "Wie ist der aktuelle Status des Services?"
→ AI ruft get_health auf und interpretiert die Antwort

User: "Zeige mir die aktiven Coin-Streams"
→ AI ruft get_streams auf und formatiert die Ergebnisse

User: "Ändere das Intervall von Phase 1 auf 10 Sekunden"
→ AI ruft update_phase mit {id: 1, interval_seconds: 10} auf
```

## Umgebungsvariablen

Konfiguration über `.env` Datei (Vorlage: `.env.example`).

### Erforderlich

| Variable | Beschreibung |
|----------|-------------|
| `DB_DSN` | PostgreSQL Connection String |
| `N8N_WEBHOOK_URL` | n8n Webhook URL für gefilterte Tokens |

### Optional (mit Defaults)

| Variable | Default | Beschreibung |
|----------|---------|-------------|
| `WS_URI` | `wss://pumpportal.fun/api/data` | WebSocket-Endpoint |
| `WS_RETRY_DELAY` | `3` | WebSocket Reconnect Verzögerung (s) |
| `WS_MAX_RETRY_DELAY` | `60` | Max. Reconnect Verzögerung (s) |
| `WS_PING_INTERVAL` | `20` | WebSocket Ping Intervall (s) |
| `WS_PING_TIMEOUT` | `10` | WebSocket Ping Timeout (s) |
| `WS_CONNECTION_TIMEOUT` | `30` | WebSocket Verbindungs-Timeout (s) |
| `N8N_WEBHOOK_METHOD` | `POST` | HTTP-Methode für Webhook |
| `N8N_RETRY_DELAY` | `5` | Webhook Retry Verzögerung (s) |
| `BATCH_SIZE` | `10` | Batch-Größe für DB-Operationen |
| `BATCH_TIMEOUT` | `30` | Batch-Timeout (s) |
| `COIN_CACHE_SECONDS` | `120` | Cache-Dauer für neue Coins (s) |
| `BAD_NAMES_PATTERN` | `test\|bot\|rug\|scam\|...` | Regex-Pattern für Spam-Filter |
| `DB_REFRESH_INTERVAL` | `10` | DB-Refresh Intervall (s) |
| `DB_RETRY_DELAY` | `5` | DB-Retry Verzögerung (s) |
| `SOL_RESERVES_FULL` | `85.0` | SOL Reserves für Graduation |
| `WHALE_THRESHOLD_SOL` | `1.0` | Whale-Schwellwert in SOL |
| `HEALTH_PORT` | `8001` | Health-Server Port |

## Datenbank

PostgreSQL mit drei Haupt-Tabellen:

| Tabelle | Beschreibung |
|---------|-------------|
| `coin_streams` | Aktive Tracking-Subscriptions (token_address, phase_id, is_active) |
| `coin_metrics` | Historische Trading-Metriken (OHLCV, Volume, Wallets) |
| `ref_coin_phases` | Phase-Definitionen für den Tracking-Lifecycle |

Schema-Initialisierung erfolgt automatisch über `db_migration.py` beim Start.

## Testing

### Backend — 201 Tests

```bash
cd backend
pip install -r requirements.test.txt
pytest tests/ -v              # Alle Tests
pytest tests/unit/ -v         # Unit-Tests
pytest tests/integration/ -v  # Integrations-Tests
pytest tests/stress/ -v       # Stress-Tests
```

### Frontend — 101 Tests

```bash
cd frontend
npm install
npm test                      # Alle Tests
npm test -- --watch           # Watch-Modus
```

## Docker Deployment

```bash
# Stack starten
docker compose up -d

# Neu bauen nach Änderungen
docker compose build --no-cache
docker compose up -d

# Status prüfen
docker compose ps

# Logs verfolgen
docker compose logs -f pump-find-backend
docker compose logs -f pump-find-frontend
```

## UI-Seiten

| Seite | Route | Beschreibung |
|-------|-------|-------------|
| Dashboard | `/` | Service-Health, Live-Stats, Verbindungsstatus |
| Metriken | `/metrics` | Prometheus-Metriken, Phasen-Verteilung |
| Phasen | `/phases` | Phasen-Management (CRUD) |
| Konfiguration | `/config` | Service-Konfiguration bearbeiten |
| Logs | `/logs` | Service-Log Viewer |
| Info | `/info` | System-Informationen |

## Dokumentation

- **[CLAUDE.md](CLAUDE.md)** — Vollständige Projekt-Dokumentation für AI-Assistenten
- **[SQL Schema](sql/)** — Datenbank-Schema Dateien
- **Swagger UI** — `http://localhost:3001/api/docs`
- **ReDoc** — `http://localhost:3001/api/redoc`

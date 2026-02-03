# System-Architektur Übersicht

## Tech-Stack

| Komponente | Technologie | Version |
|------------|-------------|---------|
| **Backend** | Python + FastAPI | 3.11 / 0.109 |
| **Datenbank** | PostgreSQL + asyncpg | 15+ / 0.29 |
| **WebSocket** | websockets | 12.0 |
| **Frontend** | React + TypeScript | 18 / 5.9 |
| **UI-Framework** | Material-UI (MUI) | 7.x |
| **State Management** | Zustand | 5.0 |
| **Build Tool** | Vite | 5.4 |
| **Container** | Docker + Nginx | 24+ / alpine |

---

## Single-Port-Architektur

Das System exponiert **nur einen Port (3001)** nach außen. Nginx fungiert als Reverse Proxy.

```
┌─────────────────────────────────────────────────────────────────┐
│                     INTERNET / COOLIFY                          │
│                        Port 3001                                │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    NGINX CONTAINER (pump-ui)                    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    nginx.conf                            │   │
│  │                                                          │   │
│  │  location / {                                            │   │
│  │      # React SPA - Static Files                          │   │
│  │      try_files $uri $uri/ /index.html;                   │   │
│  │  }                                                       │   │
│  │                                                          │   │
│  │  location /api/ {                                        │   │
│  │      # Reverse Proxy → Backend                           │   │
│  │      proxy_pass http://pump-service:8000/;               │   │
│  │  }                                                       │   │
│  │                                                          │   │
│  │  location /health {                                      │   │
│  │      # Nginx Health Check                                │   │
│  │      return 200 "healthy\n";                             │   │
│  │  }                                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Port 80 (intern) → Port 3001 (extern)                         │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               │ Docker Network (pump-network)
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                 FASTAPI CONTAINER (pump-service)                │
│                        Port 8000 (nur intern)                   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  unified_service.py                       │  │
│  │                                                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │  │
│  │  │ CoinCache   │  │ CoinFilter  │  │ UnifiedSvc  │       │  │
│  │  │ (120s)      │  │ (Spam)      │  │ (Main)      │       │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │              FastAPI REST Endpoints                  │ │  │
│  │  │  GET /health, /config, /metrics, /database/*        │ │  │
│  │  │  PUT /config, /database/phases/*                    │ │  │
│  │  │  POST /database/phases                              │ │  │
│  │  │  DELETE /database/phases/*                          │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Nicht exponiert - nur via pump-ui erreichbar                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
         ┌─────────────────────┴─────────────────────┐
         │                                           │
┌────────▼─────────┐                     ┌───────────▼───────────┐
│   PostgreSQL     │                     │   pumpportal.fun      │
│                  │                     │   WebSocket           │
│  Tables:         │                     │                       │
│  - discovered_   │                     │  wss://pumpportal.fun │
│    coins         │                     │  /api/data            │
│  - coin_streams  │                     │                       │
│  - coin_metrics  │                     │  Events:              │
│  - ref_coin_     │                     │  - create (new token) │
│    phases        │                     │  - buy/sell (trades)  │
│                  │                     │                       │
└──────────────────┘                     └───────────────────────┘
```

---

## Komponenten-Übersicht

### Backend-Komponenten (`unified_service.py`)

| Komponente | Zeilen | Beschreibung |
|------------|--------|--------------|
| **Pydantic Models** | 206-305 | Request/Response Schemas (HealthResponse, ConfigUpdateRequest, etc.) |
| **Prometheus Metrics** | 139-182 | 50+ Metriken (Counter, Gauge, Histogram) |
| **CoinCache** | 506-606 | 120-Sekunden Cache für neue Coins |
| **CoinFilter** | 608-643 | Bad Names + Spam Burst Filter |
| **UnifiedService** | 1498-2561 | Haupt-Service-Klasse mit WebSocket, DB, Trade Processing |
| **FastAPI Endpoints** | 645-1496 | Alle REST API Endpunkte |

### Frontend-Komponenten (`pump-ui/src/`)

| Komponente | Datei | Beschreibung |
|------------|-------|--------------|
| **App** | `App.tsx` | Router, Theme, Layout |
| **Dashboard** | `pages/Dashboard.tsx` | Hauptübersicht, Live-Status |
| **Metrics** | `pages/Metrics.tsx` | Prometheus Metriken, Charts |
| **Phases** | `pages/Phases.tsx` | Phase Management CRUD |
| **Config** | `pages/Config.tsx` | Runtime-Konfiguration |
| **Info** | `pages/Info.tsx` | System-Dokumentation |
| **Logs** | `pages/Logs.tsx` | Service Activity |
| **Store** | `stores/pumpStore.ts` | Zustand State Management |
| **API Client** | `services/api.ts` | Axios HTTP Client |

---

## Datenbank-Tabellen

```
┌─────────────────────┐       ┌─────────────────────┐
│  discovered_coins   │       │    coin_streams     │
├─────────────────────┤       ├─────────────────────┤
│ token_address (PK)  │◄──────│ token_address (FK)  │
│ name, symbol        │       │ current_phase_id    │
│ price_sol           │       │ is_active           │
│ market_cap_sol      │       │ is_graduated        │
│ risk_score          │       │ started_at          │
│ has_socials         │       │ ath_price_sol       │
│ ...36 Felder        │       └─────────────────────┘
└─────────────────────┘               │
                                      │ current_phase_id
                                      │
┌─────────────────────┐       ┌───────▼─────────────┐
│    coin_metrics     │       │  ref_coin_phases    │
├─────────────────────┤       ├─────────────────────┤
│ id (PK)             │       │ id (PK)             │
│ mint (FK)           │       │ name                │
│ timestamp           │       │ interval_seconds    │
│ price_open/high/    │       │ min_age_minutes     │
│   low/close         │       │ max_age_minutes     │
│ volume_sol          │       └─────────────────────┘
│ num_buys/sells      │
│ unique_wallets      │
│ ...30+ Felder       │
└─────────────────────┘
```

---

## Sicherheits-Architektur

1. **Port-Isolation**: API (8000) nur intern im Docker-Netzwerk
2. **Reverse Proxy**: Nginx als Gateway, SSL-Terminierung durch Coolify
3. **Input Validation**: Pydantic Models für alle Requests
4. **SQL Injection Prevention**: Prepared Statements via asyncpg
5. **CORS**: Aktiviert für aktuelle Domain
6. **Security Headers**: X-Frame-Options, CSP, X-XSS-Protection (via Nginx)

---

## Health Checks

| Service | Endpoint | Interval | Timeout |
|---------|----------|----------|---------|
| pump-service | `GET /health` | 30s | 10s |
| pump-ui (Nginx) | `GET /health` | 30s | 3s |
| PostgreSQL | Connection Pool | Continuous | 5s |
| pumpportal.fun | WebSocket Ping | 20s | 5s |

---

## Weiterführende Dokumentation

- [Backend im Detail](backend.md)
- [Frontend im Detail](frontend.md)
- [Datenfluss](data-flow.md)

# CLAUDE.md - Pump Finder Project

## Project Overview

**Pump Finder** is a unified cryptocurrency monitoring service that tracks new tokens on the Solana blockchain via pump.fun. Combines token discovery and metrics tracking into a single integrated system with a React UI.

## Tech Stack

- **Backend:** Python 3.11, FastAPI, asyncpg (PostgreSQL), WebSockets
- **Frontend:** React 18, TypeScript, Vite, Material-UI, Zustand
- **Testing:** pytest (Backend), vitest + MSW (Frontend)
- **Deployment:** Docker Compose, Nginx reverse proxy

## Directory Structure

```
pump-find/
├── .env                        # Environment variables (gitignored)
├── .env.example                # Template for environment setup
├── docker-compose.yaml         # Full stack orchestration
├── CLAUDE.md                   # Project documentation
├── README.md                   # Project readme
│
├── backend/                    # Python Backend (pump-find-backend)
│   ├── unified_service.py      # Main FastAPI service (2561 lines)
│   ├── db_migration.py         # Database schema initialization
│   ├── Dockerfile              # Backend Docker image
│   ├── requirements.txt        # Python dependencies
│   ├── requirements.test.txt   # Test dependencies (pytest)
│   ├── pytest.ini              # pytest configuration
│   └── tests/                  # Backend tests (201 tests)
│       ├── unit/               # Unit tests
│       ├── integration/        # Integration tests
│       └── stress/             # Stress/load tests
│
├── frontend/                   # React Frontend (pump-find-frontend)
│   ├── src/
│   │   ├── pages/              # Dashboard, Config, Metrics, Logs, Info, Phases
│   │   ├── services/api.ts     # Axios HTTP client
│   │   ├── stores/pumpStore.ts # Zustand state management
│   │   ├── types/api.ts        # TypeScript interfaces
│   │   └── __tests__/          # Frontend tests (101 tests)
│   ├── Dockerfile              # Frontend Docker image (Nginx)
│   ├── nginx.conf              # Reverse proxy configuration
│   ├── package.json            # Node dependencies
│   └── vitest.config.ts        # Vitest configuration
│
├── docs/                       # Developer documentation
│   ├── architecture/           # System architecture
│   ├── api/                    # API reference
│   ├── algorithms/             # Algorithm documentation
│   ├── database/               # Database schema & queries
│   ├── testing/                # Test documentation
│   └── deployment/             # Deployment guides
│
├── sql/                        # Database schemas
│   ├── complete_schema.sql     # Full schema
│   └── ref_coin_phase.sql      # Phase definitions
│
└── trash/                      # Archived files (can be deleted)
```

## Quick Commands

```bash
# Build and run entire stack
docker compose up -d

# Check health
curl http://localhost:3001/api/health

# View logs
docker compose logs -f pump-find-backend

# Frontend development
cd frontend && npm install && npm run dev

# Run backend tests (201 tests)
cd backend && pip install -r requirements.test.txt && pytest tests/ -v

# Run frontend tests (101 tests)
cd frontend && npm test
```

## Docker Services

| Service | Container Name | Port | Description |
|---------|----------------|------|-------------|
| pump-find-frontend | pump-find-frontend | 3001:80 | Nginx + React UI |
| pump-find-backend | pump-find-backend | 8000 (internal) | FastAPI Backend |

**Note:** Only port 3001 is exposed externally. Backend is accessed via `/api/*` proxy.

## Test Suite

### Backend (pytest) - 201 Tests
```bash
cd backend
pytest tests/ -v                    # All tests
pytest tests/unit/ -v               # Unit tests only
pytest tests/integration/ -v        # Integration tests
pytest tests/stress/ -v             # Stress tests
```

**Test Coverage:**
- `test_coin_cache.py` - Cache operations (22 tests)
- `test_coin_filter.py` - Spam filtering (26 tests)
- `test_metric_calculations.py` - Price/volume calculations (22 tests)
- `test_trade_processing.py` - Trade event handling (23 tests)
- `test_api_endpoints.py` - FastAPI routes (20 tests)
- `test_database_operations.py` - DB operations (18 tests)
- `test_websocket_connection.py` - WebSocket handling (19 tests)
- `test_zombie_detection.py` - Zombie coin detection (14 tests)
- `test_coin_stream_recovery.py` - Stream recovery (14 tests)
- `test_high_volume.py` - High volume scenarios (11 tests)
- `test_reconnection_scenarios.py` - Reconnection logic (12 tests)

### Frontend (vitest) - 101 Tests
```bash
cd frontend
npm test                            # Run all tests
npm test -- --watch                 # Watch mode
```

**Test Coverage:**
- `Dashboard.test.tsx` - Dashboard component
- `Config.test.tsx` - Configuration page
- `Metrics.test.tsx` - Metrics display
- `pumpStore.test.ts` - Zustand store
- `api.test.ts` - API service

## Key Endpoints

### Health & Metrics
- `GET /health` - Service health with detailed stats
- `GET /metrics` - Prometheus metrics

### Configuration
- `GET /config` - Current service configuration
- `PUT /config` - Update configuration

### Database & Streams
- `GET /database/streams` - Active coin tracking
- `GET /database/streams/stats` - Stream statistics by phase
- `GET /analytics/{mint}?windows=1m,5m,15m` - Coin performance

### Phase Management (CRUD)
- `GET /database/phases` - List all phases
- `POST /database/phases` - Create new phase (ID 1-98)
- `PUT /database/phases/{id}` - Update phase (triggers live-reload)
- `DELETE /database/phases/{id}` - Delete phase (migrates streams)

## Architecture

1. **WebSocket Connection** to `wss://pumpportal.fun/api/data`
2. **Coin Discovery** - Filters new tokens, sends to n8n webhook
3. **120-Second Cache** - Collects trades before activating full tracking
4. **Metrics Collection** - Stores price/volume/holder data in PostgreSQL
5. **Zombie Detection** - Deactivates stale streams automatically

## Environment Variables

Configuration via `.env` file (copy from `.env.example`):

```bash
# Required
DB_DSN=postgresql://user:pass@host:port/database
N8N_WEBHOOK_URL=https://your-n8n/webhook/endpoint

# Optional (with defaults)
COIN_CACHE_SECONDS=120
BATCH_SIZE=10
BAD_NAMES_PATTERN=test|bot|rug|scam|cant|honey|faucet
SPAM_BURST_WINDOW=30
WS_URI=wss://pumpportal.fun/api/data
HEALTH_PORT=8000
```

**Security:** The `.env` file is gitignored and contains sensitive credentials. Only `.env.example` is committed.

## Database Tables

- `coin_streams` - Active tracking subscriptions (token_address, current_phase_id, is_active)
- `coin_metrics` - Historical trading metrics (OHLCV, volume, wallets)
- `ref_coin_phases` - Phase definitions for tracking lifecycle

## Phase System

Coins progress through tracking phases based on age. Each phase has:
- **interval_seconds** - How often metrics are saved
- **min_age_minutes** - Minimum coin age for this phase
- **max_age_minutes** - Maximum coin age before advancing

### Default Phases
| ID | Name | Interval | Min Age | Max Age |
|----|------|----------|---------|---------|
| 1 | Baby Zone | 5s | 0 min | 10 min |
| 2 | Survival Zone | 15s | 10 min | 120 min |
| 3 | Mature Zone | 15s | 120 min | 240 min |
| 99 | Finished | - | - | - |
| 100 | Graduated | - | - | - |

### Phase Management Features
- **Add phases** via UI or `POST /database/phases`
- **Edit phases** with live-reload of active streams
- **Delete phases** with automatic stream migration
- **System phases** (99, 100) are protected and cannot be modified
- **Validation**: interval >= 1s, max_age > min_age, min 1 regular phase required

## Code Conventions

- German variable names and comments
- Async/await patterns throughout
- Pydantic models for validation
- Type hints on all functions
- MUI responsive breakpoints: `{ xs: ..., sm: ..., md: ... }`

## UI Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Service health, live stats, connection status |
| Metriken | `/metrics` | Prometheus metrics, phase distribution |
| Phasen | `/phases` | Phase management (CRUD) |
| Info | `/info` | System information |
| Konfiguration | `/config` | Service configuration |
| Logs | `/logs` | Service log viewer |

## Mobile Responsive Design

All UI components are optimized for mobile:
- Dashboard: Responsive icons, typography, gaps
- Metrics: Responsive charts, grid layouts, padding
- Phases: Responsive table, inline editing
- Config: Adaptive form layouts
- Logs: Button wrapping, container height adjustments

## Docker Deployment

```bash
# Start full stack
docker compose up -d

# Rebuild after changes
docker compose build --no-cache
docker compose up -d

# Check status
docker compose ps
docker compose logs -f pump-find-backend
```

## Troubleshooting

### Database Zombie Cleanup
```sql
-- In container or locally with DB access
UPDATE coin_streams SET is_active = false
WHERE is_active = true
AND started_at < NOW() - INTERVAL '2 hours'
AND NOT EXISTS (SELECT 1 FROM coin_metrics cm WHERE cm.mint = token_address);
```

### Check Service Health
```bash
curl -s http://localhost:3001/api/health | python3 -m json.tool
```

### Phase Management via CLI
```bash
# List phases
curl -s http://localhost:3001/api/database/phases | jq '.phases'

# Create new phase
curl -X POST http://localhost:3001/api/database/phases \
  -H "Content-Type: application/json" \
  -d '{"name": "Extended Zone", "interval_seconds": 30, "min_age_minutes": 240, "max_age_minutes": 480}'

# Update phase (triggers live-reload)
curl -X PUT http://localhost:3001/api/database/phases/1 \
  -H "Content-Type: application/json" \
  -d '{"interval_seconds": 10}'

# Delete phase (streams migrate to next phase)
curl -X DELETE http://localhost:3001/api/database/phases/4
```

---

## Developer Documentation

Vollständige Entwickler-Dokumentation unter `docs/`:

### Architektur
- **[docs/architecture/overview.md](docs/architecture/overview.md)** - System-Diagramme, Tech-Stack, Single-Port-Architektur
- **[docs/architecture/backend.md](docs/architecture/backend.md)** - UnifiedService Klasse (2561 Zeilen) im Detail
- **[docs/architecture/frontend.md](docs/architecture/frontend.md)** - React-Architektur, 6 Seiten, Zustand Store
- **[docs/architecture/data-flow.md](docs/architecture/data-flow.md)** - WebSocket → Cache → DB → n8n Datenfluss

### API-Referenz
- **[docs/api/endpoints.md](docs/api/endpoints.md)** - Alle 15+ REST-Endpunkte mit Request/Response Schemas
- **[docs/api/websocket.md](docs/api/websocket.md)** - pumpportal.fun WebSocket-Protokoll

### Algorithmen
- **[docs/algorithms/coin-discovery.md](docs/algorithms/coin-discovery.md)** - CoinFilter, 120s Cache, n8n Batching
- **[docs/algorithms/trade-processing.md](docs/algorithms/trade-processing.md)** - OHLCV, Whale Detection, ATH-Tracking
- **[docs/algorithms/phase-management.md](docs/algorithms/phase-management.md)** - Lifecycle, CRUD, Live-Reload
- **[docs/algorithms/zombie-detection.md](docs/algorithms/zombie-detection.md)** - Stale Streams, Force-Resubscribe

### Datenbank
- **[docs/database/schema.md](docs/database/schema.md)** - 4 Tabellen, 20+ Indices, ER-Diagramm
- **[docs/database/queries.md](docs/database/queries.md)** - Wichtige SQL-Queries mit Erklärungen

### Testing
- **[docs/testing/backend.md](docs/testing/backend.md)** - 201 pytest Tests, Fixtures, Mock-Strategien
- **[docs/testing/frontend.md](docs/testing/frontend.md)** - 101 vitest + MSW Tests

### Deployment
- **[docs/deployment/docker.md](docs/deployment/docker.md)** - Docker-Konfiguration, Commands, Troubleshooting
- **[docs/deployment/monitoring.md](docs/deployment/monitoring.md)** - 50+ Prometheus Metriken, Grafana

### Referenz
- **[docs/glossary.md](docs/glossary.md)** - Begriffslexikon (OHLCV, ATH, Bonding Curve, etc.)

---

## Documentation Maintenance

**WICHTIG:** Bei Code-Änderungen MUSS die entsprechende Dokumentation aktualisiert werden!

| Änderung an... | Dokumentation aktualisieren |
|----------------|----------------------------|
| `backend/unified_service.py` | `docs/architecture/backend.md`, `docs/algorithms/*` |
| API-Endpunkte | `docs/api/endpoints.md` |
| Datenbank-Schema | `docs/database/schema.md`, `docs/database/queries.md` |
| Frontend-Komponenten | `docs/architecture/frontend.md` |
| Docker-Konfiguration | `docs/deployment/docker.md` |
| Prometheus-Metriken | `docs/deployment/monitoring.md` |
| Tests | `docs/testing/backend.md` oder `docs/testing/frontend.md` |

**Dokumentations-Checkliste bei PRs:**
1. Code-Referenzen (Zeilennummern) noch korrekt?
2. Neue Features/Endpunkte dokumentiert?
3. Geänderte Algorithmen aktualisiert?
4. Glossar erweitert falls neue Begriffe?

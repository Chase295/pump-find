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
├── unified_service.py          # Main FastAPI service (discovery + metrics)
├── db_migration.py             # Database schema initialization
├── requirements.unified.txt    # Python dependencies
├── requirements.test.txt       # Test dependencies (pytest)
├── pytest.ini                  # pytest configuration
├── docker-compose.yaml         # Full stack orchestration
├── .env                        # Environment variables (gitignored)
├── .env.example                # Template for environment setup
├── tests/                      # Backend tests (201 tests)
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── stress/                 # Stress/load tests
├── pump-ui/                    # React TypeScript frontend
│   ├── src/pages/              # Dashboard, Config, Metrics, Logs, Info
│   ├── src/services/api.ts     # Axios HTTP client
│   ├── src/stores/pumpStore.ts # Zustand state management
│   ├── src/__tests__/          # Frontend tests (101 tests)
│   │   ├── components/         # Component tests
│   │   ├── stores/             # Store tests
│   │   ├── services/           # API tests
│   │   └── mocks/              # MSW mock handlers
│   └── vitest.config.ts        # Vitest configuration
├── sql/                        # Database schemas
├── scripts/                    # Testing utilities
└── docs/                       # Additional documentation
```

## Quick Commands

```bash
# Build and run entire stack
docker compose up -d

# Check health
curl http://localhost:3001/api/health

# View logs
docker compose logs -f pump-service

# Frontend development
cd pump-ui && npm install && npm run dev

# Run backend tests (201 tests)
pip install -r requirements.test.txt
pytest tests/ -v

# Run frontend tests (101 tests)
cd pump-ui && npm test
```

## Test Suite

### Backend (pytest) - 201 Tests
```bash
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
cd pump-ui
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

- `GET /health` - Service health with detailed stats
- `GET /metrics` - Prometheus metrics
- `GET /config` / `PUT /config` - Configuration management
- `GET /database/streams` - Active coin tracking
- `GET /analytics/{mint}?windows=1m,5m,15m` - Coin performance

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

- `coin_streams` - Active tracking subscriptions (token_address, phase, is_active)
- `coin_metrics` - Historical trading metrics (OHLCV, volume, wallets)
- `tracking_phases` - Phase definitions for tracking lifecycle

## Ports

| Service | Port | Description |
|---------|------|-------------|
| pump-ui (Nginx) | 3001 | UI + API Proxy |
| pump-service | 8000 | FastAPI (internal) |

**Note:** Only port 3001 is exposed externally. The backend is accessed via `/api/*` proxy.

## Code Conventions

- German variable names and comments
- Async/await patterns throughout
- Pydantic models for validation
- Type hints on all functions
- MUI responsive breakpoints: `{ xs: ..., sm: ..., md: ... }`

## Mobile Responsive Design

All UI components are optimized for mobile:
- Dashboard: Responsive icons, typography, gaps
- Metrics: Responsive charts, grid layouts, padding
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
docker compose logs -f
```

## Troubleshooting

### Database Zombie Cleanup
```python
# In container or locally with DB access
UPDATE coin_streams SET is_active = false
WHERE is_active = true
AND started_at < NOW() - INTERVAL '2 hours'
AND NOT EXISTS (SELECT 1 FROM coin_metrics cm WHERE cm.mint = token_address);
```

### Check Service Health
```bash
curl -s http://localhost:3001/api/health | python3 -m json.tool
```

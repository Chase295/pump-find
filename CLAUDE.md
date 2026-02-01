# CLAUDE.md - Pump Finder Project

## Project Overview

**Pump Finder** is a unified cryptocurrency monitoring service that tracks new tokens on the Solana blockchain via pump.fun. Combines token discovery and metrics tracking into a single integrated system with a React UI.

## Tech Stack

- **Backend:** Python 3.11, FastAPI, asyncpg (PostgreSQL), WebSockets
- **Frontend:** React 18, TypeScript, Vite, Material-UI, Zustand
- **Deployment:** Docker Compose, Nginx reverse proxy

## Directory Structure

```
├── unified_service.py          # Main FastAPI service (discovery + metrics)
├── db_migration.py             # Database schema initialization
├── requirements.unified.txt    # Python dependencies
├── docker-compose.yaml         # Full stack orchestration
├── pump-ui/                    # React TypeScript frontend
│   ├── src/pages/              # Dashboard, Config, Metrics, Logs, Info
│   ├── src/services/api.ts     # Axios HTTP client
│   └── src/stores/pumpStore.ts # Zustand state management
├── sql/                        # Database schemas
├── scripts/                    # Testing utilities
└── docs/                       # Additional documentation
```

## Quick Commands

```bash
# Build and run entire stack
docker-compose up -d

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f pump-service

# Frontend development
cd pump-ui && npm install && npm run dev
```

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

## Environment Variables

Key settings in `.env`:
- `DB_DSN` - PostgreSQL connection string
- `N8N_WEBHOOK_URL` - n8n integration endpoint
- `BAD_NAMES_PATTERN` - Regex for filtering spam tokens
- `COIN_CACHE_SECONDS` - Cache duration (default: 120)

## Database Tables

- `discovered_coins` - Token discovery data
- `coin_metrics` - Historical trading metrics
- `coin_streams` - Active tracking subscriptions

## Ports

| Service | Port |
|---------|------|
| FastAPI | 8000 |
| React UI | 3001 |
| Nginx | 80 |

## Code Conventions

- German variable names and comments
- Async/await patterns throughout
- Pydantic models for validation
- Type hints on all functions

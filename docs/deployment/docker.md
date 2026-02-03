# Docker Deployment

Dokumentation der Docker-Konfiguration und Deployment-Prozesse.

---

## Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                     INTERNET / COOLIFY                          │
│                        Port 3001                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    NGINX CONTAINER (pump-ui)                    │
│                        Port 80 (intern)                         │
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
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Docker Network (pump-network)
                           │
┌──────────────────────────▼──────────────────────────────────────┐
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
└─────────────────────────────────────────────────────────────────┘
```

---

## docker-compose.yaml

```yaml
services:
  pump-ui:
    build:
      context: ./pump-ui
      dockerfile: Dockerfile
    container_name: pump-ui
    restart: unless-stopped
    ports:
      - "3001:80"  # EINZIGER externer Port
    depends_on:
      - pump-service
    networks:
      - pump-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  pump-service:
    build:
      context: .
      dockerfile: Dockerfile.unified
    container_name: pump-service
    restart: unless-stopped
    expose:
      - "8000"  # Nur intern
    env_file:
      - .env
    volumes:
      - ./config:/app/config:rw
    networks:
      - pump-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  pump-network:
    driver: bridge

volumes:
  pump-config:
    driver: local
```

### Wichtige Punkte

| Aspekt | Erklärung |
|--------|-----------|
| **Single Port** | Nur Port 3001 ist extern exponiert |
| **Reverse Proxy** | Nginx leitet `/api/*` an pump-service:8000 weiter |
| **Internal Network** | pump-service ist nur über Docker Network erreichbar |
| **Health Checks** | Beide Services haben Health Checks |
| **Volumes** | Config-Verzeichnis für persistente Einstellungen |

---

## Dockerfile.unified (Backend)

```dockerfile
# Vereinter Pump Service - Discovery + Metrics
FROM python:3.11-slim

WORKDIR /app

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten
COPY requirements.unified.txt .
RUN pip install --no-cache-dir -r requirements.unified.txt

# Anwendung kopieren
COPY unified_service.py .
COPY db_migration.py .

# Config-Verzeichnis erstellen
RUN mkdir -p /app/config

# Port freigeben
EXPOSE 8000

# Health-Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start-Kommando (FastAPI mit Uvicorn)
CMD ["uvicorn", "unified_service:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## pump-ui/Dockerfile (Frontend)

```dockerfile
# Stage 1: Build
FROM node:22-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install --include=dev
COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine

# Nginx Konfiguration
COPY nginx.conf /etc/nginx/nginx.conf

# Build-Artefakte
COPY --from=builder /app/dist /usr/share/nginx/html

# Health Check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost/health || exit 1

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## nginx.conf

```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/javascript application/javascript application/json;

    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;

        # React Router - SPA Fallback
        location / {
            try_files $uri $uri/ /index.html;
        }

        # API Proxy
        location /api/ {
            proxy_pass http://pump-service:8000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health Check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # Static Asset Caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

---

## Commands

### Stack starten

```bash
# Erstmalig (mit Build)
docker compose up -d --build

# Neustart
docker compose up -d

# Mit Logs
docker compose up
```

### Stack stoppen

```bash
# Normal stoppen
docker compose down

# Mit Volumes löschen
docker compose down -v
```

### Rebuild

```bash
# Einzelnen Service rebuilden
docker compose build pump-service
docker compose build pump-ui

# Alle Services ohne Cache rebuilden
docker compose build --no-cache

# Rebuild und starten
docker compose up -d --build
```

### Logs

```bash
# Alle Logs
docker compose logs -f

# Einzelner Service
docker compose logs -f pump-service
docker compose logs -f pump-ui

# Letzte 100 Zeilen
docker compose logs --tail=100 pump-service
```

### Status

```bash
# Container-Status
docker compose ps

# Health-Check
curl http://localhost:3001/api/health

# Ressourcen-Nutzung
docker stats pump-service pump-ui
```

### Shell-Zugang

```bash
# Backend Container
docker compose exec pump-service /bin/bash

# Frontend Container (Alpine)
docker compose exec pump-ui /bin/sh

# Python REPL im Backend
docker compose exec pump-service python
```

---

## Environment Variables

### .env Datei

```bash
# Datenbank
DB_DSN=postgresql://user:password@host:5432/pump_finder

# n8n Integration
N8N_WEBHOOK_URL=https://your-n8n.com/webhook/endpoint
N8N_WEBHOOK_METHOD=POST

# Cache & Batching
COIN_CACHE_SECONDS=120
BATCH_SIZE=10
BATCH_TIMEOUT=30

# Filter
BAD_NAMES_PATTERN=test|bot|rug|scam|cant|honey|faucet
SPAM_BURST_WINDOW=30

# WebSocket
WS_URI=wss://pumpportal.fun/api/data
WS_PING_INTERVAL=20
WS_PING_TIMEOUT=10

# API Port
HEALTH_PORT=8000
```

### Sichere Handhabung

- `.env` ist in `.gitignore`
- Nur `.env.example` wird commited
- Sensible Daten nie in docker-compose.yaml

---

## Troubleshooting

### Container startet nicht

```bash
# Logs prüfen
docker compose logs pump-service

# Health-Check manuell
docker compose exec pump-service curl http://localhost:8000/health
```

### API nicht erreichbar

```bash
# Nginx-Logs prüfen
docker compose logs pump-ui

# Nginx-Konfiguration prüfen
docker compose exec pump-ui cat /etc/nginx/nginx.conf

# Backend-Status prüfen
docker compose exec pump-ui curl http://pump-service:8000/health
```

### Datenbank-Verbindung

```bash
# DB_DSN prüfen
docker compose exec pump-service env | grep DB_DSN

# Verbindung testen
docker compose exec pump-service python -c "
import asyncio
import asyncpg
import os

async def test():
    conn = await asyncpg.connect(os.environ['DB_DSN'])
    print(await conn.fetchval('SELECT 1'))
    await conn.close()

asyncio.run(test())
"
```

### WebSocket-Probleme

```bash
# WebSocket-Status in Health
curl -s http://localhost:3001/api/health | jq '.ws_connected'

# Reconnects prüfen
curl -s http://localhost:3001/api/health | jq '.reconnect_count'
```

### Volume-Probleme

```bash
# Volumes auflisten
docker volume ls

# Volume inspizieren
docker volume inspect pump-find_pump-config

# Config-Verzeichnis prüfen
docker compose exec pump-service ls -la /app/config
```

---

## Coolify Deployment

### Voraussetzungen

1. Coolify-Instanz mit Docker
2. GitHub Repository verbunden
3. PostgreSQL-Datenbank verfügbar

### Konfiguration

1. **Repository:** Zeigt auf GitHub Repo
2. **Build:** Docker Compose
3. **Port:** 3001
4. **Environment:** In Coolify UI konfigurieren

### Domain

- Coolify konfiguriert automatisch SSL
- Domain zeigt auf Port 3001
- `/api/*` wird an Backend proxied

---

## Weiterführende Dokumentation

- [Monitoring](monitoring.md) - Prometheus Metriken
- [Backend-Architektur](../architecture/backend.md) - Service-Details
- [API-Endpunkte](../api/endpoints.md) - Verfügbare Endpoints

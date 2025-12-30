# 🚀 PROFESSIONAL SINGLE-PORT DEPLOYMENT

## 🎯 Übersicht

**Ein Service. Ein Port. Alles funktioniert.**

Diese professionelle Lösung kombiniert API und UI in einem einzigen Docker-Container, der nur **Port 3001** exponiert.

### 🏗️ Architektur

```
🌐 Externer Reverse Proxy (z.B. Coolify)
    ↓
📦 pump-unified Container (Port 3001)
├── 🖥️  nginx (Port 80 intern)
│   ├── / → UI (statische Dateien)
│   ├── /api/* → FastAPI (Port 8000 intern)
│   └── /health → nginx Health Check
└── 🔌 FastAPI (Port 8000 intern)
    ├── /api/health → Health Status
    ├── /api/config → Konfiguration
    └── /api/docs → API Dokumentation
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# config/.env erstellen
cp .env.example config/.env
# Oder verwende bestehende config/.env
```

### 2. Build & Deploy

```bash
# Single-Command Deployment
docker-compose -f docker-compose.professional.yml up -d --build

# Logs prüfen
docker-compose -f docker-compose.professional.yml logs -f
```

### 3. Externer Reverse Proxy

Konfiguriere deinen Reverse Proxy (z.B. Coolify), um alles zu `ihre-server-ip:3001` weiterzuleiten:

```nginx
# Coolify Reverse Proxy Config
server {
    listen 80;
    server_name deine-domain.com;

    location / {
        proxy_pass http://ihre-server-ip:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📡 Zugriff

### Lokal
- **UI:** `http://localhost:3001`
- **API:** `http://localhost:3001/api/health`
- **API Docs:** `http://localhost:3001/api/docs`

### Extern (über Reverse Proxy)
- **UI:** `https://deine-domain.com`
- **API:** `https://deine-domain.com/api/health`
- **API Docs:** `https://deine-domain.com/api/docs`

## 🔧 Konfiguration

### Environment Variables

```bash
# Datenbank
DB_DSN=postgresql://user:pass@host:5432/db

# WebSocket
WS_URI=wss://pumpportal.fun/api/data

# Coin Cache
COIN_CACHE_SECONDS=300

# n8n Integration
N8N_WEBHOOK_URL=https://n8n.example.com/webhook/...

# Batching
BATCH_SIZE=10
BATCH_TIMEOUT=30

# Spam Protection
SPAM_BURST_WINDOW=60
BAD_NAMES_PATTERN=.*(?i)(shit|fuck|damn).*
```

### Health Checks

```bash
# Container Health
curl http://localhost:3001/health

# API Health
curl http://localhost:3001/api/health

# Vollständiger Status
curl http://localhost:3001/api/health | jq
```

## 🛠️ Development

### UI Änderungen

```bash
# UI bauen
cd pump-ui
npm run build

# Container neu bauen
docker-compose -f docker-compose.professional.yml up -d --build
```

### API Änderungen

```bash
# Container neu starten
docker-compose -f docker-compose.professional.yml restart
```

## 📊 Monitoring

### Logs

```bash
# Alle Logs
docker-compose -f docker-compose.professional.yml logs -f

# Nur API
docker-compose -f docker-compose.professional.yml logs -f pump-unified | grep uvicorn

# Nur nginx
docker-compose -f docker-compose.professional.yml logs -f pump-unified | grep nginx
```

### Metriken

```bash
# Prometheus Metriken
curl http://localhost:3001/metrics
```

## 🎯 Vorteile dieser Lösung

✅ **Ein Port:** Nur 3001 exponiert
✅ **Einfach:** Ein Container, ein Service
✅ **Professionell:** nginx + FastAPI Kombination
✅ **SSL-Ready:** Externer Reverse Proxy übernimmt SSL
✅ **Skalierbar:** nginx als Load Balancer möglich
✅ **Monitorable:** Vollständige Health Checks

## 🔄 Migration von alter Lösung

```bash
# Alte Container stoppen
docker-compose down

# Neue Lösung starten
docker-compose -f docker-compose.professional.yml up -d --build

# Reverse Proxy anpassen (nur Port ändern)
# Von: pump-service:8001 + pump-ui:3001
# Zu:   pump-unified:3001
```

---

**Perfekt für Produktion!** 🎉

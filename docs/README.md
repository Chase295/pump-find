# Pump Finder - Entwickler-Dokumentation

Vollständige technische Dokumentation für Entwickler, die das Pump Finder System verstehen, warten oder erweitern möchten.

---

## Projekt-Übersicht

**Pump Finder** ist ein Echtzeit-Monitoring-System für neue Tokens auf der Solana Blockchain via pump.fun. Das System:

1. **Entdeckt** neue Tokens über WebSocket-Verbindung zu pumpportal.fun
2. **Filtert** Spam und verdächtige Tokens (Bad Names, Burst-Detection)
3. **Cached** neue Tokens für 120 Sekunden zur Validierung
4. **Trackt** Live-Trades mit OHLCV-Metriken, Whale-Detection und Dev-Tracking
5. **Speichert** Zeitreihen-Daten in PostgreSQL
6. **Visualisiert** alles in einer React-basierten Web-UI

---

## Dokumentations-Struktur

### Architektur
- **[architecture/overview.md](architecture/overview.md)** - System-Diagramme, Tech-Stack, Single-Port-Architektur
- **[architecture/backend.md](architecture/backend.md)** - UnifiedService, CoinCache, CoinFilter im Detail
- **[architecture/frontend.md](architecture/frontend.md)** - React-Komponenten, Zustand Store, Responsive Design
- **[architecture/data-flow.md](architecture/data-flow.md)** - Kompletter Datenfluss von WebSocket bis Datenbank

### API-Referenz
- **[api/endpoints.md](api/endpoints.md)** - Alle 15+ REST API Endpunkte mit Beispielen
- **[api/websocket.md](api/websocket.md)** - pumpportal.fun WebSocket-Protokoll

### Algorithmen
- **[algorithms/coin-discovery.md](algorithms/coin-discovery.md)** - Token-Entdeckung, Filter, Cache
- **[algorithms/trade-processing.md](algorithms/trade-processing.md)** - OHLCV, Whale, Dev-Tracking
- **[algorithms/phase-management.md](algorithms/phase-management.md)** - Lifecycle, Phase-Upgrades
- **[algorithms/zombie-detection.md](algorithms/zombie-detection.md)** - Stale Stream Detection

### Datenbank
- **[database/schema.md](database/schema.md)** - Alle Tabellen, Felder, Indices
- **[database/queries.md](database/queries.md)** - Wichtige SQL-Queries erklärt
- **[SCHEMA_UEBERSICHT.md](SCHEMA_UEBERSICHT.md)** - Detaillierte Schema-Übersicht (Legacy)

### Testing
- **[testing/backend.md](testing/backend.md)** - 201 pytest Tests, Fixtures, Mocks
- **[testing/frontend.md](testing/frontend.md)** - 101 vitest Tests, MSW

### Deployment
- **[deployment/docker.md](deployment/docker.md)** - Docker-Konfiguration, Commands
- **[deployment/monitoring.md](deployment/monitoring.md)** - 50+ Prometheus Metriken

### Referenz
- **[glossary.md](glossary.md)** - Begriffslexikon (OHLCV, ATH, Bonding Curve, etc.)
- **[websocket_schema_vergleich.md](websocket_schema_vergleich.md)** - WebSocket vs SQL Schema (Legacy)

---

## Quick Start für Entwickler

### Projekt klonen und starten
```bash
git clone https://github.com/Chase295/pump-find.git
cd pump-find

# Environment konfigurieren
cp .env.example .env
# .env bearbeiten: DB_DSN, N8N_WEBHOOK_URL setzen

# Docker starten
docker compose up -d

# Health prüfen
curl http://localhost:3001/api/health
```

### Lokale Entwicklung
```bash
# Backend (Python)
pip install -r requirements.unified.txt
python unified_service.py

# Frontend (React)
cd pump-ui
npm install
npm run dev
```

### Tests ausführen
```bash
# Backend (201 Tests)
pytest tests/ -v

# Frontend (101 Tests)
cd pump-ui && npm test
```

---

## Kritische Dateien

| Datei | Beschreibung |
|-------|--------------|
| `unified_service.py` | Haupt-Backend (2561 Zeilen) - alle Algorithmen, APIs |
| `pump-ui/src/pages/*.tsx` | 6 UI-Seiten |
| `pump-ui/src/stores/pumpStore.ts` | Zustand State Management |
| `pump-ui/src/services/api.ts` | API-Client |
| `sql/complete_schema.sql` | Datenbank-Schema |
| `docker-compose.yaml` | Docker-Orchestrierung |
| `CLAUDE.md` | Projekt-Instruktionen für KI-Assistenten |

---

## Architektur auf einen Blick

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERNET (Port 3001)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     NGINX (pump-ui)                         │
│  ┌─────────────────┐    ┌─────────────────────────────┐    │
│  │  React App      │    │  Reverse Proxy              │    │
│  │  (Static Files) │    │  /api/* → pump-service:8000 │    │
│  └─────────────────┘    └─────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                 FASTAPI (pump-service:8000)                 │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐               │
│  │ CoinCache │  │CoinFilter │  │ WebSocket │               │
│  │ (120s)    │  │(Bad Names)│  │ (trades)  │               │
│  └───────────┘  └───────────┘  └───────────┘               │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         │                                   │
┌────────▼────────┐              ┌───────────▼───────────┐
│   PostgreSQL    │              │   pumpportal.fun      │
│  (coin_streams, │              │   WebSocket           │
│   coin_metrics) │              │   (Live Trades)       │
└─────────────────┘              └───────────────────────┘
```

---

## Dokumentation aktuell halten

Bei Code-Änderungen bitte die entsprechende Dokumentation aktualisieren:

| Änderung | Zu aktualisierende Docs |
|----------|-------------------------|
| Neuer API-Endpunkt | `api/endpoints.md` |
| Neuer Algorithmus | `algorithms/*.md` |
| Schema-Änderung | `database/schema.md` |
| Neue Prometheus-Metrik | `deployment/monitoring.md` |
| Neue UI-Komponente | `architecture/frontend.md` |
| Neue Konfiguration | `CLAUDE.md` + relevante Docs |

---

## Weitere Dokumentation

- **[../CLAUDE.md](../CLAUDE.md)** - Projekt-Instruktionen (für KI-Assistenten)
- **[../README.md](../README.md)** - Haupt-README

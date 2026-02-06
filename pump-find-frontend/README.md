# Pump Find Frontend

Professionelle Web-UI für die Verwaltung und Überwachung von Pump Find.

## Überblick

Diese React + TypeScript + Vite Anwendung bietet eine moderne Weboberfläche zur:

- **Live-Monitoring** des Service-Status
- **Konfigurationsverwaltung** (n8n, Datenbank, Cache)
- **Log-Überwachung** mit Auto-Refresh
- **Responsive Design** für Desktop & Mobile

## Technologie-Stack

- **React 18** - Moderne UI-Bibliothek
- **TypeScript** - Type-Sichere Entwicklung
- **Vite** - Schneller Build-Tool
- **Material-UI (MUI)** - Komponenten-Bibliothek
- **Recharts** - Datenvisualisierung
- **React Router** - Client-Side Routing
- **Axios** - HTTP-Client
- **Zustand** - State-Management

## Schnellstart

### Entwicklung
```bash
# Dependencies installieren
npm install

# Entwicklungsserver starten
npm run dev

# Öffne http://localhost:3000
```

### Build für Production
```bash
# Build erstellen
npm run build

# Vorschau des Builds
npm run preview
```

### Docker Deployment
```bash
# Mit vereintem Service starten
docker-compose -f docker-compose.ui.yml up -d

# UI ist verfügbar auf http://localhost:3000
```

## Projekt-Struktur

```
pump-find-frontend/
├── src/
│   ├── components/     # Wiederverwendbare Komponenten
│   ├── pages/         # Hauptseiten (Dashboard, Config, Logs)
│   ├── services/      # API-Integration
│   ├── stores/        # Zustand-Management
│   ├── types/         # TypeScript-Definitionen
│   └── utils/         # Hilfsfunktionen
├── public/            # Statische Assets
├── Dockerfile         # Docker-Image
├── nginx.conf         # Nginx-Konfiguration
├── .env               # Environment-Konfiguration
└── package.json       # Dependencies & Scripts
```

## Features

### Dashboard
- **Live-Status** aller Service-Komponenten
- **Cache-Statistiken** (aktive Coins, abgelaufene)
- **Discovery-Metriken** (Coins gefunden, n8n-Status)
- **Tracking-Übersicht** (aktive Coins, Trades)
- **Uptime-Anzeige** und Service-Gesundheit

### Konfiguration
- **n8n-Einstellungen** (URL, HTTP-Methode)
- **Datenbank-Konfiguration** (DSN, Connection-String)
- **Performance-Parameter** (Cache-Zeit, Batch-Größe)
- **Live-Updates** mit Validierung

### Logs
- **Service-Activity** Monitoring
- **Auto-Refresh** konfigurierbar
- **Log-Level** Indikatoren
- **Download-Funktion** für Log-Files

## Deployment

### Docker-Compose
```yaml
# Vollständiges Setup mit UI + Service
version: '3.8'
services:
  pump-find-frontend:  # React UI (Port 3000)
  pump-find-backend:   # FastAPI Service (Port 8000)
```

### Einzeln starten
```bash
# Nur UI entwickeln (Service muss separat laufen)
npm run dev

# UI mit Service
docker-compose -f docker-compose.ui.yml up -d
```

# Glossar

Begriffslexikon für das Pump Finder Projekt.

---

## A

### ATH (All-Time-High)
Der höchste Preis, den ein Token jemals erreicht hat. Wird in `coin_streams.ath_price_sol` gespeichert und bei jedem Trade aktualisiert.

### Aktivierung
Prozess, bei dem ein Coin aus dem 120s-Cache in das aktive Tracking überführt wird. Erfordert mindestens 3 Trades.

### asyncpg
Asynchroner PostgreSQL-Treiber für Python. Verwendet für alle Datenbankoperationen im Backend.

---

## B

### Bad Names Filter
Regex-basierter Filter, der Coins mit verdächtigen Namen blockiert (z.B. "test", "scam", "bot").

### Batch
Gruppierung von Daten für effiziente Verarbeitung. Verwendet für:
- n8n Discovery Buffer (10 Coins oder 30s)
- WebSocket Subscriptions (50 Coins alle 2s)
- Metriken-Flush (pro Phase-Intervall)

### Bonding Curve
AMM-Kurve auf pump.fun, die den Token-Preis basierend auf Supply/Demand bestimmt.

```
Preis = vSolInBondingCurve / vTokensInBondingCurve
```

### Buffer
Temporärer Speicher für Trade-Daten pro Coin zwischen Metric-Flushes. Enthält OHLCV, Volume, Wallets etc.

---

## C

### Cache (120s)
Temporärer Speicher für neue Coins vor Aktivierung. Dient zur Validierung (echte Aktivität).

### Coolify
Self-hosted PaaS für Docker-Deployment. Verwaltet SSL, Domain, Container.

### Counter (Prometheus)
Metrik-Typ, der nur steigen kann. Beispiel: `coins_received_total`.

### CRUD
Create, Read, Update, Delete - Standard-Operationen für Phase Management.

---

## D

### Dev (Developer/Creator)
Der Ersteller eines Tokens. Dessen Wallet-Adresse wird in `trader_public_key` gespeichert.

### Dev Sold
Menge an SOL, die der Token-Ersteller verkauft hat. Indikator für "Dev Dump".

### Discovery
Prozess der Token-Erkennung über WebSocket `create` Events.

---

## F

### Flush
Schreiben von gepufferten Daten in die Datenbank. Erfolgt basierend auf Phase-Intervall.

---

## G

### Gauge (Prometheus)
Metrik-Typ, der steigen und fallen kann. Beispiel: `cache_size`.

### Graduation
Migration eines Tokens von pump.fun zu Raydium bei ~99.5% gefüllter Bonding Curve.

---

## H

### Histogram (Prometheus)
Metrik-Typ für Verteilungen. Beispiel: `db_query_duration_seconds`.

---

## L

### Lamports
Kleinste Einheit von SOL (1 SOL = 1.000.000.000 Lamports).

---

## M

### Micro Trade
Trade unter 0.01 SOL. Kann auf Bot-Aktivität hinweisen.

### Mint
Eindeutige Token-Adresse (44 Zeichen Base58). Primary Key für alle Token-Tabellen.

### MSW (Mock Service Worker)
Test-Library zum Mocken von HTTP-Requests in Frontend-Tests.

---

## N

### n8n
Workflow-Automation-Tool. Empfängt entdeckte Coins via Webhook für weitere Verarbeitung.

---

## O

### OHLCV
Open, High, Low, Close, Volume - Standard-Format für Preisdaten:
- **O**pen: Erster Preis im Intervall
- **H**igh: Höchster Preis
- **L**ow: Niedrigster Preis
- **C**lose: Letzter Preis
- **V**olume: Handelsvolumen

---

## P

### Phase
Tracking-Stufe mit definiertem Intervall und Altersbereich:
- Phase 1 (Baby): 0-10 min, 5s Intervall
- Phase 2 (Survival): 10-120 min, 15s Intervall
- Phase 3 (Mature): 120-240 min, 15s Intervall
- Phase 99 (Finished): Timeout
- Phase 100 (Graduated): Raydium Migration

### Prometheus
Monitoring-System. Metriken werden unter `/api/metrics` exponiert.

### pump.fun
Solana-basierte Plattform für Token-Launches mit Bonding Curve.

### pumpportal.fun
WebSocket-API-Anbieter für Echtzeit-Daten von pump.fun.

---

## R

### Raydium
Solana DEX (Decentralized Exchange). Tokens migrieren nach Graduation hierhin.

### Reconnect (Exponential Backoff)
Strategie für WebSocket-Neuverbindung: 1s → 2s → 4s → ... → 60s max.

### Reverse Proxy
Nginx leitet `/api/*` Requests an das Backend weiter.

---

## S

### Single-Port-Architektur
Nur Port 3001 ist extern exponiert. Backend nur über Nginx erreichbar.

### Spam Burst
Erkennung von mehrfachen Token-Erstellungen mit gleichem Namen/Symbol innerhalb von 30s.

### Stream
Aktives Token-Tracking in `coin_streams`. Enthält Phase, Status, ATH.

### Subscription
WebSocket-Abonnement für Token-Trade-Events.

---

## T

### TTL (Time To Live)
Lebensdauer im Cache (120 Sekunden für neue Coins).

---

## U

### Unified Service
Haupt-Backend-Komponente (`unified_service.py`), die Discovery und Metrics kombiniert.

### Unique Wallets
Anzahl unterschiedlicher Trader-Adressen pro Intervall.

---

## V

### vSolInBondingCurve
Virtuelles SOL in der Bonding Curve. Teil der Preisberechnung.

### vTokensInBondingCurve
Virtuelle Tokens in der Bonding Curve. Teil der Preisberechnung.

---

## W

### Watchlist
In-Memory Dictionary aller aktiv getrackten Coins mit Buffer und Metadaten.

### Whale
Trader mit großem Volumen (>= 1.0 SOL pro Trade).

### WebSocket
Bidirektionale Verbindung zu pumpportal.fun für Echtzeit-Events.

---

## Z

### Zombie (Stream)
Inaktiver Stream, der keine Trades mehr empfängt. Wird durch Watchdog erkannt und per Force-Resubscribe reaktiviert.

### Zustand
React State Management Library. Verwendet für globalen UI-State.

---

## Abkürzungen

| Abkürzung | Bedeutung |
|-----------|-----------|
| ATH | All-Time-High |
| API | Application Programming Interface |
| DB | Database |
| DSN | Data Source Name |
| OHLCV | Open, High, Low, Close, Volume |
| PK | Primary Key |
| SOL | Solana |
| TTL | Time To Live |
| UI | User Interface |
| WS | WebSocket |

---

## Weiterführende Dokumentation

- [Architektur-Übersicht](architecture/overview.md)
- [Datenfluss](architecture/data-flow.md)
- [API-Endpunkte](api/endpoints.md)

# Datenbank-Schema

Vollständige Dokumentation aller PostgreSQL-Tabellen.

---

## Übersicht

```
┌─────────────────────┐       ┌─────────────────────┐
│  discovered_coins   │       │    coin_streams     │
├─────────────────────┤       ├─────────────────────┤
│ token_address (PK)  │◄──────│ token_address (FK)  │
│ name, symbol        │       │ current_phase_id    │──┐
│ price_sol           │       │ is_active           │  │
│ market_cap_sol      │       │ is_graduated        │  │
│ risk_score          │       │ started_at          │  │
│ has_socials         │       │ ath_price_sol       │  │
│ ...36 Felder        │       └─────────────────────┘  │
└─────────────────────┘               │                │
                                      │ current_phase_id
                                      │                │
┌─────────────────────┐       ┌───────▼─────────────┐  │
│    coin_metrics     │       │  ref_coin_phases    │◄─┘
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

## 1. discovered_coins

**Zweck:** Haupttabelle für alle entdeckten Tokens

**Zeilen:** ~1500+ (wächst kontinuierlich)

### Struktur

```sql
CREATE TABLE discovered_coins (
    -- IDENTIFIKATION
    token_address VARCHAR(64) NOT NULL PRIMARY KEY,
    blockchain_id INT NOT NULL DEFAULT 1,
    symbol VARCHAR(30),
    name VARCHAR(255),
    token_decimals INT,
    token_supply NUMERIC(30, 6),
    deploy_platform VARCHAR(50),

    -- TRANSAKTIONS-INFORMATIONEN
    signature VARCHAR(88),
    trader_public_key VARCHAR(44),

    -- BONDING CURVE & POOL
    bonding_curve_key VARCHAR(44),
    pool_address VARCHAR(64),
    pool_type VARCHAR(20) DEFAULT 'pump',
    v_tokens_in_bonding_curve NUMERIC(30, 6),
    v_sol_in_bonding_curve NUMERIC(20, 6),

    -- INITIAL BUY
    initial_buy_sol NUMERIC(20, 6),
    initial_buy_tokens NUMERIC(30, 6),

    -- ZEITSTEMPEL
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    token_created_at TIMESTAMP WITH TIME ZONE,

    -- PREIS & MARKET CAP
    price_sol NUMERIC(30, 18),
    market_cap_sol NUMERIC(20, 2),
    liquidity_sol NUMERIC(20, 6),

    -- GRADUATION
    open_market_cap_sol NUMERIC(20, 2) DEFAULT 85000,
    phase_id INT,

    -- STATUS FLAGS
    is_mayhem_mode BOOLEAN DEFAULT FALSE,
    is_graduated BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    -- RISIKO & ANALYSE
    risk_score INT,
    top_10_holders_pct NUMERIC(5, 2),
    has_socials BOOLEAN DEFAULT FALSE,
    social_count INT DEFAULT 0,
    metadata_is_mutable BOOLEAN,
    mint_authority_enabled BOOLEAN,
    image_hash VARCHAR(64),

    -- METADATA & SOCIAL MEDIA
    metadata_uri TEXT,
    description TEXT,
    image_url TEXT,
    twitter_url TEXT,
    telegram_url TEXT,
    website_url TEXT,
    discord_url TEXT,

    -- MANAGEMENT
    final_outcome VARCHAR(20) DEFAULT 'PENDING',
    classification VARCHAR(50) DEFAULT 'UNKNOWN',
    status_note VARCHAR(255)
);
```

### Wichtige Felder

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `token_address` | VARCHAR(64) | Mint-Adresse (Primary Key) |
| `trader_public_key` | VARCHAR(44) | Creator-Wallet |
| `price_sol` | NUMERIC(30,18) | Aktueller Preis in SOL |
| `market_cap_sol` | NUMERIC(20,2) | Market Cap in SOL |
| `social_count` | INT | Anzahl Social Links (0-4) |
| `has_socials` | BOOLEAN | Hat mindestens 1 Social Link |
| `is_graduated` | BOOLEAN | Zu Raydium migriert |
| `is_active` | BOOLEAN | Noch aktiv |

### Indices

```sql
-- Basis-Indexe
CREATE INDEX idx_dc_active ON discovered_coins(is_active);
CREATE INDEX idx_dc_graduated ON discovered_coins(is_graduated);
CREATE INDEX idx_dc_discovered ON discovered_coins(discovered_at DESC);
CREATE INDEX idx_dc_created_at ON discovered_coins(token_created_at);

-- Transaktions-Indexe
CREATE INDEX idx_dc_trader ON discovered_coins(trader_public_key);
CREATE INDEX idx_dc_signature ON discovered_coins(signature);

-- Market Cap Index
CREATE INDEX idx_dc_market_cap_sol ON discovered_coins(market_cap_sol DESC);

-- Risiko-Indexe
CREATE INDEX idx_dc_risk_score ON discovered_coins(risk_score);
CREATE INDEX idx_dc_social_count ON discovered_coins(social_count);
CREATE INDEX idx_dc_image_hash ON discovered_coins(image_hash);
```

---

## 2. coin_streams

**Zweck:** Aktive Token-Tracking-Streams

**Zeilen:** ~200-500 aktive, ~1500+ total

### Struktur

```sql
CREATE TABLE coin_streams (
    id BIGSERIAL PRIMARY KEY,
    token_address VARCHAR(64) NOT NULL UNIQUE,
    current_phase_id INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    is_graduated BOOLEAN DEFAULT false,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    ath_price_sol NUMERIC(30, 18),
    ath_timestamp TIMESTAMP WITH TIME ZONE
);
```

### Felder

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `id` | BIGSERIAL | Auto-increment ID |
| `token_address` | VARCHAR(64) | Mint-Adresse (Unique) |
| `current_phase_id` | INTEGER | Aktuelle Tracking-Phase (1-3, 99, 100) |
| `is_active` | BOOLEAN | Stream aktiv? |
| `is_graduated` | BOOLEAN | Token graduiert? |
| `started_at` | TIMESTAMP | Stream-Startzeit |
| `ath_price_sol` | NUMERIC | All-Time-High Preis |
| `ath_timestamp` | TIMESTAMP | ATH-Zeitpunkt |

### Indices

```sql
CREATE INDEX idx_coin_streams_token_address ON coin_streams(token_address);
CREATE INDEX idx_coin_streams_phase_id ON coin_streams(current_phase_id);
CREATE INDEX idx_coin_streams_active ON coin_streams(is_active);
CREATE INDEX idx_coin_streams_graduated ON coin_streams(is_graduated);
```

### Stream-Zustände

| is_active | is_graduated | current_phase_id | Bedeutung |
|-----------|--------------|------------------|-----------|
| true | false | 1-3 | Aktives Tracking |
| false | false | 99 | Timeout (Finished) |
| false | true | 100 | Raydium Migration |

---

## 3. ref_coin_phases

**Zweck:** Phasen-Definitionen für Tracking

**Zeilen:** 5 (fix)

### Struktur

```sql
CREATE TABLE ref_coin_phases (
    id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    interval_seconds INT NOT NULL,
    min_age_minutes INT NOT NULL,
    max_age_minutes INT NOT NULL
);
```

### Default-Daten

```sql
INSERT INTO ref_coin_phases VALUES
(1, 'Baby Zone', 5, 0, 10),
(2, 'Survival Zone', 30, 10, 60),
(3, 'Mature Zone', 60, 60, 1440),
(99, 'Finished', 0, 1440, 999999),
(100, 'Graduated', 0, 1440, 999999);
```

### Felder

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `id` | INT | Phase-ID (1-3: regulär, 99/100: system) |
| `name` | VARCHAR(50) | Anzeigename |
| `interval_seconds` | INT | Metrik-Flush-Intervall |
| `min_age_minutes` | INT | Minimales Coin-Alter |
| `max_age_minutes` | INT | Maximales Coin-Alter |

---

## 4. coin_metrics

**Zweck:** Zeitreihen-Daten für OHLCV und Trading-Statistiken

**Zeilen:** Viele (wächst schnell)

### Struktur (erweitert im Service)

```sql
CREATE TABLE coin_metrics (
    id SERIAL PRIMARY KEY,
    mint VARCHAR(64) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,

    -- OHLCV
    price_open NUMERIC(30, 18),
    price_high NUMERIC(30, 18),
    price_low NUMERIC(30, 18),
    price_close NUMERIC(30, 18),

    -- Volume
    volume_sol NUMERIC(20, 6),
    volume_buy_sol NUMERIC(20, 6),
    volume_sell_sol NUMERIC(20, 6),

    -- Trade Counts
    num_buys INT DEFAULT 0,
    num_sells INT DEFAULT 0,
    micro_trades INT DEFAULT 0,

    -- Wallets
    unique_wallets INT DEFAULT 0,

    -- Whale Stats
    whale_buys INT DEFAULT 0,
    whale_sells INT DEFAULT 0,
    whale_buy_volume NUMERIC(20, 6),
    whale_sell_volume NUMERIC(20, 6),

    -- Dev Tracking
    dev_sold_sol NUMERIC(20, 6),

    -- Market Data
    market_cap_sol NUMERIC(20, 2),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Wichtige Felder

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `mint` | VARCHAR(64) | Token-Adresse |
| `timestamp` | TIMESTAMPTZ | Metrik-Zeitstempel |
| `price_open/high/low/close` | NUMERIC | OHLCV-Preise |
| `volume_sol` | NUMERIC | Gesamt-Volumen |
| `unique_wallets` | INT | Eindeutige Trader |
| `whale_buys/sells` | INT | Whale-Trades (>= 1 SOL) |
| `dev_sold_sol` | NUMERIC | Vom Creator verkauft |

### Indices

```sql
CREATE INDEX idx_coin_metrics_mint ON coin_metrics(mint);
CREATE INDEX idx_coin_metrics_timestamp ON coin_metrics(timestamp DESC);
CREATE INDEX idx_coin_metrics_mint_timestamp ON coin_metrics(mint, timestamp DESC);
```

---

## Beziehungen

### discovered_coins ↔ coin_streams

```sql
-- Implizite Beziehung über token_address
SELECT dc.*, cs.current_phase_id, cs.is_active
FROM discovered_coins dc
LEFT JOIN coin_streams cs ON dc.token_address = cs.token_address;
```

### coin_streams ↔ ref_coin_phases

```sql
-- Phase-Details für aktive Streams
SELECT cs.*, rcp.name as phase_name, rcp.interval_seconds
FROM coin_streams cs
JOIN ref_coin_phases rcp ON cs.current_phase_id = rcp.id
WHERE cs.is_active = true;
```

### coin_streams ↔ coin_metrics

```sql
-- Metriken für einen Stream
SELECT cm.*
FROM coin_metrics cm
JOIN coin_streams cs ON cm.mint = cs.token_address
WHERE cs.token_address = 'So11111...'
ORDER BY cm.timestamp DESC;
```

---

## Datentypen-Erklärung

| PostgreSQL-Typ | Verwendung | Beispiel |
|----------------|------------|----------|
| `VARCHAR(64)` | Token-Adressen | `So111...` (44 Zeichen) |
| `NUMERIC(30, 18)` | Preise mit hoher Präzision | `0.000000000038500000` |
| `NUMERIC(20, 6)` | Volumen in SOL | `45.500000` |
| `NUMERIC(20, 2)` | Market Cap | `12345.67` |
| `TIMESTAMPTZ` | Zeitstempel mit Zone | `2025-01-18 12:00:00+00` |
| `BIGSERIAL` | Auto-increment IDs | `1, 2, 3, ...` |

---

## Wartung

### Alte Metriken löschen

```sql
-- Metriken älter als 30 Tage
DELETE FROM coin_metrics
WHERE timestamp < NOW() - INTERVAL '30 days';
```

### Inaktive Streams bereinigen

```sql
-- Streams ohne Metriken seit 4 Stunden
UPDATE coin_streams
SET is_active = false, current_phase_id = 99
WHERE is_active = true
  AND started_at < NOW() - INTERVAL '4 hours'
  AND NOT EXISTS (
    SELECT 1 FROM coin_metrics cm
    WHERE cm.mint = token_address
    AND cm.timestamp > NOW() - INTERVAL '1 hour'
  );
```

### Statistiken

```sql
-- Tabellen-Größen
SELECT
  relname as table_name,
  n_live_tup as row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;
```

---

## Weiterführende Dokumentation

- [Wichtige Queries](queries.md) - SQL-Beispiele
- [API-Endpunkte](../api/endpoints.md) - Datenbank-Zugriff via API
- [Phase Management](../algorithms/phase-management.md) - Phasen-Logik
